"""
Base Worker Module

Provides base classes and utilities for background task workers.
Supports both Celery and FastAPI BackgroundTasks.
"""
import logging
from typing import Optional, Any, Dict, Callable
from functools import wraps
try:
    from celery import Task
    from celery.exceptions import MaxRetriesExceededError
    CELERY_AVAILABLE = True
except ImportError:
    class Task:
        def __init__(self, *args, **kwargs): pass
        def on_failure(self, *args, **kwargs): pass
        def on_retry(self, *args, **kwargs): pass
        def on_success(self, *args, **kwargs): pass
    
    class MaxRetriesExceededError(Exception):
        pass
    CELERY_AVAILABLE = False

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseWorkerTask(Task):
    """
    Base class for Celery worker tasks.
    
    Provides:
    - Automatic retry on failure
    - Proper logging
    - Error handling
    """
    
    # Retry settings
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    max_retries = 3
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            f"Task {self.name} failed: {exc}",
            extra={"task_id": task_id, "args": args, "kwargs": kwargs}
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            f"Task {self.name} retrying: {exc}",
            extra={"task_id": task_id, "retry_count": self.request.retries}
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(
            f"Task {self.name} succeeded",
            extra={"task_id": task_id, "retval": retval}
        )
        super().on_success(retval, task_id, args, kwargs)


def worker_task(func: Callable) -> Task:
    """
    Decorator to convert a function into a Celery task.
    
    Usage:
        @worker_task
        def my_task(arg1, arg2):
            # task logic
            return result
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    # Create Celery task
    task = Task(wrapper)
    task.__dict__.update(BaseWorkerTask.__dict__)
    
    return task


class WorkerResult:
    """Standardized result from worker tasks."""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        **extra
    ):
        self.success = success
        self.data = data
        self.error = error
        self.extra = extra
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        result.update(self.extra)
        return result


# ==================== FastAPI Background Tasks ====================

class BackgroundTaskRunner:
    """
    Utility class for running tasks in FastAPI BackgroundTasks.
    
    Provides retry logic and error handling.
    """
    
    @staticmethod
    def run_with_retry(
        func: Callable,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> WorkerResult:
        """
        Run a function with retry logic.
        
        Args:
            func: Function to run
            *args: Positional arguments
            max_retries: Maximum number of retries
            **kwargs: Keyword arguments
            
        Returns:
            WorkerResult
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                return WorkerResult(success=True, data=result)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                )
        
        return WorkerResult(
            success=False,
            error=str(last_error)
        )
    
    @staticmethod
    def run_task(
        task_func: Callable,
        *args,
        **kwargs
    ):
        """
        Run a task function (designed for BackgroundTasks.add_task).
        
        Args:
            task_func: Function to run
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        try:
            task_func(*args, **kwargs)
            logger.info(f"Background task completed: {task_func.__name__}")
        except Exception as e:
            logger.error(
                f"Background task failed: {task_func.__name__}",
                error=str(e)
            )


# ==================== Celery Configuration ====================

def get_celery_config() -> Dict[str, Any]:
    """
    Get Celery configuration with task priority queues and routing.
    
    Returns:
        Celery configuration dictionary
    """
    if not CELERY_AVAILABLE:
        return {}

    from app.core.config import settings
    try:
        from kombu import Queue
    except ImportError:
        logger.warning("Kombu not found, Celery configuration will be incomplete")
        return {}
    
    return {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
        "task_track_started": settings.CELERY_TASK_TRACK_STARTED,
        "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
        "task_soft_time_limit": settings.CELERY_TASK_TIME_LIMIT - 30,
        "worker_prefetch_multiplier": 1,
        "worker_max_tasks_per_child": 100,
        
        # Priority Queues
        "task_queues": (
            Queue("high", routing_key="high"),
            Queue("default", routing_key="default"),
            Queue("low", routing_key="low"),
        ),
        "task_default_queue": "default",
        "task_default_exchange": "tasks",
        "task_default_routing_key": "default",
        
        # Task Routing
        "task_routes": {
            # High priority: Time-sensitive user-facing tasks
            "resume_parse_worker.process": {"queue": "high"},
            "email_worker.process": {"queue": "high"},
            
            # Default priority: Standard processing
            "ats_analysis_worker.process": {"queue": "default"},
            "resume_embedding_worker.process": {"queue": "default"},
            
            # Low priority: Background ingestion and long-running analysis
            "job_ingestion_worker.process": {"queue": "low"},
            "ats_analysis_worker.batch_process": {"queue": "low"},
        },
    }


def create_celery_app():
    """
    Create and configure Celery application.
    
    Returns:
        Configured Celery app
    """
    if not CELERY_AVAILABLE:
        logger.warning("Celery not available, background tasks will not be available")
        return None
        
    from celery import Celery
    
    app = Celery("grobsai")
    app.config_from_object(get_celery_config())
    
    # Auto-discover tasks
    app.autodiscover_tasks(["app.workers"])
    
    return app


# ==================== Task Queue Helpers ====================

def enqueue_task(
    task_name: str,
    priority: Optional[str] = None,
    *args,
    **kwargs
) -> Optional[str]:
    """
    Enqueue a task to Celery.
    
    If Celery is not available or connection fails, 
    falls back to synchronous execution in development/testing environments.
    
    Args:
        task_name: Full task name (e.g., "app.workers.parse_resume")
        priority: Optional queue name (high, default, low)
        *args: Task arguments
        **kwargs: Task keyword arguments
        
    Returns:
        Task ID or None if Celery not available (executed sync)
    """
    if not CELERY_AVAILABLE:
        logger.warning(f"Celery not available, falling back to sync execution for {task_name}.")
        return _execute_sync(task_name, *args, **kwargs)

    try:
        from celery import current_app
        # Check if broker is reachable
        with current_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
            
        send_kwargs = {"args": args, "kwargs": kwargs}
        if priority:
            send_kwargs["queue"] = priority
            
        result = current_app.send_task(task_name, **send_kwargs)
        return result.id
    except Exception as e:
        logger.warning(f"Failed to enqueue task to Celery: {e}. Falling back to sync execution.")
        return _execute_sync(task_name, *args, **kwargs)


def _execute_sync(task_name: str, *args, **kwargs) -> Optional[str]:
    """Fallback to synchronous execution."""
    try:
        # Dynamically import the worker module and call the function
        module_name, func_name = task_name.rsplit('.', 1)
        import importlib
        # Adjust module name to match actual path if needed
        # In our case "email_worker.process" -> "app.workers.email_worker.process"
        if not module_name.startswith('app.workers.'):
            full_module_name = f"app.workers.{module_name}"
        else:
            full_module_name = module_name
            
        module = importlib.import_module(full_module_name)
        func = getattr(module, func_name)
        func(*args, **kwargs)
        return "sync_execution"
    except Exception as sync_e:
        logger.error(f"Failed to execute task synchronously: {sync_e}")
        return None


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a Celery task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status dictionary
    """
    if not CELERY_AVAILABLE:
        return {
            "id": task_id,
            "status": "COMPLETED" if task_id == "sync_execution" else "UNKNOWN",
            "ready": True if task_id == "sync_execution" else False,
            "successful": True if task_id == "sync_execution" else None
        }

    try:
        from celery import current_app
        result = current_app.AsyncResult(task_id)
        return {
            "id": result.id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.ready() else None,
            "error": str(result.info) if result.failed() else None
        }
    except Exception as e:
        logger.warning(f"Failed to get task status: {e}")
        return {
            "id": task_id,
            "status": "UNKNOWN",
            "error": str(e)
        }

