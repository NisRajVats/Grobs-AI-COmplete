"""
Simple In-Memory Caching Utility for FastAPI
"""
import time
import functools
import logging
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)

class MemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            item = self._cache[key]
            if item['expiry'] is None or item['expiry'] > time.time():
                return item['value']
            else:
                # Expired
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL (seconds)."""
        expiry = time.time() + ttl if ttl else None
        self._cache[key] = {
            'value': value,
            'expiry': expiry
        }
    
    def clear(self):
        """Clear all cache."""
        self._cache = {}

# Global cache instance
cache_instance = MemoryCache()

def cache_response(ttl: int = 60, use_user_id: bool = True):
    """
    Decorator to cache function results.
    Note: Only use for pure functions or GET request handlers.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            # Special handling for current_user to use user_id in cache key
            cache_parts = [func.__module__, func.__name__]
            
            for k, v in kwargs.items():
                if k == "current_user" and hasattr(v, "id"):
                    cache_parts.append(f"user_{v.id}")
                elif k == "db":
                    continue # Skip DB session
                else:
                    cache_parts.append(f"{k}_{str(v)}")
            
            cache_key = ":".join(cache_parts)
            
            cached_val = cache_instance.get(cache_key)
            if cached_val is not None:
                logger.info(f"Returning cached result for {func.__name__}")
                return cached_val
            
            # Call the original function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache the result
            cache_instance.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Helper to avoid import issues
import asyncio
