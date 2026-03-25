"""
Observability Module - Structured logging, metrics, and tracing.

Includes:
- Structured logging configuration
- Prometheus metrics
- OpenTelemetry tracing
- Error monitoring integration
"""
import os
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

# Sentry
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


# ==================== Structured Logging ====================

class StructuredLogger:
    """
    Structured logger that outputs JSON format for log aggregation.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Add JSON handler if not already added
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            handler = logging.StreamHandler()
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs):
        """Log with structured data."""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "grobsai-backend",
            **kwargs
        }
        
        getattr(self.logger, level)(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        self._log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("debug", message, **kwargs)
    
    def log_request(self, method: str, path: str, status_code: int, duration: float, **kwargs):
        """Log HTTP request in structured format."""
        self.info(
            f"{method} {path}",
            event="http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add extra fields
        if hasattr(record, "event"):
            log_data["event"] = record.event
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "service"):
            log_data["service"] = record.service
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# ==================== Prometheus Metrics ====================

class Metrics:
    """Prometheus metrics collector."""
    
    def __init__(self):
        self._initialized = False
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Business metrics
        self.resume_uploads_total = Counter(
            'resume_uploads_total',
            'Total resume uploads'
        )
        
        self.resume_parses_total = Counter(
            'resume_parses_total',
            'Total resume parses',
            ['status']
        )
        
        self.job_matches_total = Counter(
            'job_matches_total',
            'Total job matches',
            ['status']
        )
        
        self.ats_analyses_total = Counter(
            'ats_analyses_total',
            'Total ATS analyses',
            ['status']
        )
        
        # Active users gauge
        self.active_users = Gauge(
            'active_users',
            'Number of active users'
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'queue_size',
            'Current queue size',
            ['queue_name']
        )
        
        self._initialized = True
    
    def increment_http_request(self, method: str, endpoint: str, status: int):
        """Increment HTTP request counter."""
        if self._initialized:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
    
    def observe_http_duration(self, method: str, endpoint: str, duration: float):
        """Observe HTTP request duration."""
        if self._initialized:
            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def increment_resume_upload(self):
        """Increment resume upload counter."""
        if self._initialized:
            self.resume_uploads_total.inc()
    
    def increment_resume_parse(self, status: str):
        """Increment resume parse counter."""
        if self._initialized:
            self.resume_parses_total.labels(status=status).inc()
    
    def increment_job_match(self, status: str):
        """Increment job match counter."""
        if self._initialized:
            self.job_matches_total.labels(status=status).inc()
    
    def increment_ats_analysis(self, status: str):
        """Increment ATS analysis counter."""
        if self._initialized:
            self.ats_analyses_total.labels(status=status).inc()
    
    def set_active_users(self, count: int):
        """Set active users gauge."""
        if self._initialized:
            self.active_users.set(count)
    
    def set_queue_size(self, queue_name: str, size: int):
        """Set queue size gauge."""
        if self._initialized:
            self.queue_size.labels(queue_name=queue_name).set(size)


# Global metrics instance
metrics = Metrics()


# ==================== OpenTelemetry Tracing ====================

def init_telemetry(app=None):
    """Initialize OpenTelemetry tracing."""
    if not TELEMETRY_AVAILABLE:
        return None
    
    # Set up tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    
    # Add OTLP exporter (configure endpoint via environment)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        )
    
    # Instrument FastAPI if app provided
    if app:
        FastAPIInstrumentor.instrument_app(app)
    
    return trace.get_tracer(__name__)


def trace_operation(name: str):
    """Decorator to trace function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not TELEMETRY_AVAILABLE:
                return func(*args, **kwargs)
            
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


# ==================== Sentry Integration ====================

def init_sentry():
    """Initialize Sentry for error monitoring."""
    if not SENTRY_AVAILABLE:
        return
    
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        # Set profile_session_sample_rate to capture 100%
        # of CPU profiles
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENVIRONMENT", "development"),
        release=f"grobsai@{os.getenv('VERSION', '1.0.0')}"
    )


# ==================== Utility Functions ====================

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def setup_logging(level: str = "INFO"):
    """Setup structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(message)s'  # Use JSON formatter
    )


# Export metrics endpoint for Prometheus
def get_metrics():
    """Get Prometheus metrics in text format."""
    if PROMETHEUS_AVAILABLE:
        return generate_latest()
    return b""

