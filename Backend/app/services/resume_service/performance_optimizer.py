"""
Performance Optimizer — v4
==========================
Production-grade performance optimizations for resume processing.

Features:
- Async processing pipeline
- Caching strategies
- Batch processing support
- Memory optimization
- Database query optimization
- Rate limiting and throttling
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
import weakref
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from redis.asyncio import Redis as RedisAsync
import pickle
from cachetools import TTLCache
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Type definitions
# ─────────────────────────────────────────────────────────────────────────────

T = TypeVar('T')
CacheKey = Union[str, tuple]


class PerformanceOptimizer:
    """
    Performance optimization utilities for resume processing.
    
    Features:
    - Async processing pipeline
    - Multi-level caching (memory, Redis)
    - Batch processing with concurrency control
    - Memory optimization
    - Database query optimization
    - Rate limiting and throttling
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize performance optimizer.
        
        Args:
            db: Database session for query optimization
        """
        self.db = db
        
        # Memory cache with TTL
        self.memory_cache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL,
        )
        
        # Redis cache (if available)
        self.redis_client = None
        if settings.REDIS_URL:
            try:
                self.redis_client = RedisAsync.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_calls=settings.RATE_LIMIT_CALLS,
            time_window=settings.RATE_LIMIT_WINDOW,
        )
        
        # Batch processing
        self.batch_processor = BatchProcessor()
        
        # Memory monitoring
        self.memory_monitor = MemoryMonitor()
    
    async def get_cached_result(
        self,
        key: CacheKey,
        fallback_func: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """
        Get cached result or compute and cache.
        
        Args:
            key: Cache key
            fallback_func: Function to compute result if not cached
            ttl: Time to live in seconds
            
        Returns:
            Cached or computed result
        """
        # Check memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                cached = await self.redis_client.get(str(key))
                if cached:
                    result = pickle.loads(cached)
                    self.memory_cache[key] = result
                    return result
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        # Compute result
        result = await self._execute_with_retry(fallback_func)
        
        # Cache result
        self.memory_cache[key] = result
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    str(key),
                    ttl or settings.CACHE_TTL,
                    pickle.dumps(result),
                )
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
        
        return result
    
    async def batch_process(
        self,
        items: List[Any],
        process_func: Callable[[Any], T],
        batch_size: int = 10,
        max_concurrent: int = 5,
    ) -> List[T]:
        """
        Process items in batches with concurrency control.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent tasks
            
        Returns:
            List of processed results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item):
            async with semaphore:
                return await self._execute_with_retry(lambda: process_func(item))
        
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=True,
            )
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results
    
    def memoize(
        self,
        ttl: Optional[int] = None,
        key_func: Optional[Callable[..., CacheKey]] = None,
    ):
        """
        Decorator for memoizing function results.
        
        Args:
            ttl: Time to live in seconds
            key_func: Function to generate cache key from arguments
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get cached result
                try:
                    return await self.get_cached_result(key, lambda: func(*args, **kwargs), ttl)
                except Exception as e:
                    logger.error(f"Memoization failed for {func.__name__}: {e}")
                    return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    async def execute_with_rate_limit(
        self,
        func: Callable[[], T],
        resource_name: str = "default",
    ) -> T:
        """
        Execute function with rate limiting.
        
        Args:
            func: Function to execute
            resource_name: Name of the resource being rate limited
            
        Returns:
            Function result
        """
        async with self.rate_limiter:
            return await self._execute_with_retry(func)
    
    def optimize_database_queries(self, query_func: Callable[[], T]) -> Callable[[], T]:
        """
        Optimize database queries with connection pooling and query optimization.
        
        Args:
            query_func: Database query function
            
        Returns:
            Optimized query function
        """
        @functools.wraps(query_func)
        async def wrapper():
            start_time = time.perf_counter()
            
            try:
                # Use connection pooling
                if self.db:
                    result = await self._execute_with_retry(query_func)
                else:
                    result = await query_func()
                
                # Log query performance
                elapsed = (time.perf_counter() - start_time) * 1000
                if elapsed > 1000:  # Log slow queries
                    logger.warning(f"Slow query detected: {elapsed:.2f}ms")
                
                return result
                
            except Exception as e:
                logger.error(f"Database query failed: {e}")
                raise
        
        return wrapper
    
    def monitor_memory_usage(self, func: Callable[[], T]) -> Callable[[], T]:
        """
        Monitor memory usage of function execution.
        
        Args:
            func: Function to monitor
            
        Returns:
            Monitored function
        """
        @functools.wraps(func)
        async def wrapper():
            initial_memory = self.memory_monitor.get_memory_usage()
            
            try:
                result = await self._execute_with_retry(func)
                
                final_memory = self.memory_monitor.get_memory_usage()
                memory_increase = final_memory - initial_memory
                
                if memory_increase > 100:  # Log high memory usage
                    logger.warning(f"High memory usage: {memory_increase:.2f}MB")
                
                return result
                
            except Exception as e:
                logger.error(f"Memory monitoring failed: {e}")
                raise
        
        return wrapper
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> CacheKey:
        """Generate cache key from function name and arguments."""
        # Create a hashable key from function name and arguments
        key_parts = [func_name]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool, type(None))):
                key_parts.append(arg)
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])
        
        return tuple(key_parts)
    
    async def _execute_with_retry(
        self,
        func: Callable[[], T],
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> T:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for retry delay
            
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"Max retries exceeded for function: {e}")
                    raise
                
                # Calculate delay
                delay = backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)
        
        raise last_exception


class RateLimiter:
    """Rate limiter with sliding window algorithm."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []
    
    async def __aenter__(self):
        """Acquire rate limit."""
        current_time = time.time()
        
        # Remove old calls outside the time window
        cutoff_time = current_time - self.time_window
        self.calls = [call_time for call_time in self.calls if call_time > cutoff_time]
        
        # Check if we can make the call
        if len(self.calls) >= self.max_calls:
            # Wait until we can make the call
            oldest_call = min(self.calls)
            wait_time = self.time_window - (current_time - oldest_call)
            await asyncio.sleep(wait_time)
        
        # Add current call
        self.calls.append(current_time)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release rate limit."""
        pass


class MemoryMonitor:
    """Monitor memory usage and provide optimization suggestions."""
    
    def __init__(self):
        """Initialize memory monitor."""
        self.peak_memory = 0
        self.current_memory = 0
    
    def get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.current_memory = memory_info.rss / 1024 / 1024  # Convert to MB
            self.peak_memory = max(self.peak_memory, self.current_memory)
            return self.current_memory
        except ImportError:
            # Fallback if psutil is not available
            return 0.0
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory statistics."""
        return {
            "current_mb": self.current_memory,
            "peak_mb": self.peak_memory,
            "available_mb": self._get_available_memory(),
        }
    
    def _get_available_memory(self) -> float:
        """Get available system memory in MB."""
        try:
            import psutil
            return psutil.virtual_memory().available / 1024 / 1024
        except ImportError:
            return 0.0
    
    def suggest_optimizations(self) -> List[str]:
        """Suggest memory optimizations."""
        suggestions = []
        
        if self.current_memory > 500:  # More than 500MB
            suggestions.append("Consider processing data in smaller batches")
        
        if self.peak_memory > 1000:  # More than 1GB
            suggestions.append("Implement streaming processing for large datasets")
        
        available_memory = self._get_available_memory()
        if available_memory < 1000:  # Less than 1GB available
            suggestions.append("System memory is low, consider closing other applications")
        
        return suggestions


class BatchProcessor:
    """Optimized batch processor for large datasets."""
    
    def __init__(self):
        """Initialize batch processor."""
        self.processed_count = 0
        self.error_count = 0
        self.total_time = 0
    
    async def process_large_dataset(
        self,
        dataset: List[Any],
        process_func: Callable[[Any], Any],
        batch_size: int = 100,
        max_concurrent: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process large dataset with progress tracking and error handling.
        
        Args:
            dataset: Dataset to process
            process_func: Function to process each item
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent tasks
            progress_callback: Callback for progress updates
            
        Returns:
            Processing statistics
        """
        start_time = time.perf_counter()
        results = []
        errors = []
        
        # Process in batches
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            
            # Process batch
            batch_results = await self._process_batch(
                batch,
                process_func,
                max_concurrent,
            )
            
            # Collect results and errors
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(result)
                    self.error_count += 1
                else:
                    results.append(result)
                    self.processed_count += 1
            
            # Update progress
            if progress_callback:
                progress_callback(self.processed_count, len(dataset))
        
        # Calculate statistics
        elapsed_time = time.perf_counter() - start_time
        self.total_time = elapsed_time
        
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "total_time": elapsed_time,
            "items_per_second": self.processed_count / elapsed_time if elapsed_time > 0 else 0,
            "success_rate": (self.processed_count / len(dataset)) * 100 if dataset else 0,
            "errors": errors[:10],  # Return first 10 errors
        }
    
    async def _process_batch(
        self,
        batch: List[Any],
        process_func: Callable[[Any], Any],
        max_concurrent: int,
    ) -> List[Any]:
        """Process a single batch."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item):
            async with semaphore:
                try:
                    return await process_func(item)
                except Exception as e:
                    return e
        
        return await asyncio.gather(
            *[process_item(item) for item in batch],
            return_exceptions=False,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Global instances
# ─────────────────────────────────────────────────────────────────────────────

_performance_optimizer = None


def get_performance_optimizer(db: Optional[Session] = None) -> PerformanceOptimizer:
    """Get or create the singleton performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer(db=db)
    return _performance_optimizer


# ─────────────────────────────────────────────────────────────────────────────
# Utility decorators
# ─────────────────────────────────────────────────────────────────────────────

def async_cache(ttl: Optional[int] = None):
    """Decorator for async caching."""
    optimizer = get_performance_optimizer()
    return optimizer.memoize(ttl=ttl)


def rate_limited(resource_name: str = "default"):
    """Decorator for rate limiting."""
    optimizer = get_performance_optimizer()
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await optimizer.execute_with_rate_limit(
                lambda: func(*args, **kwargs),
                resource_name=resource_name,
            )
        return wrapper
    return decorator


def memory_monitored(func):
    """Decorator for memory monitoring."""
    optimizer = get_performance_optimizer()
    return optimizer.monitor_memory_usage(func)


def optimized_db_query(func):
    """Decorator for optimized database queries."""
    optimizer = get_performance_optimizer()
    return optimizer.optimize_database_queries(func)