"""
Logging Configuration Module

Centralized logging setup for the GrobsAI Backend.
Provides structured logging with different handlers for different environments.
"""
import logging
import sys
from typing import Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output in development.
    Adds ANSI color codes to log levels.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Log message format
        
    Returns:
        Configured root logger
    """
    # Use settings if not provided
    level = log_level or settings.LOG_LEVEL
    file_path = log_file or settings.log_file_path
    fmt = log_format or settings.LOG_FORMAT
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (with colors for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Use colored formatter for console in development
    if settings.ENVIRONMENT == "development":
        console_formatter = ColoredFormatter(fmt)
    else:
        console_formatter = logging.Formatter(fmt)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (rotating)
    try:
        # Ensure log directory exists
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        # Standard formatter for file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
    except (OSError, PermissionError) as e:
        root_logger.warning(f"Could not create file handler: {e}")
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter that adds contextual information.
    """
    
    def process(self, msg, kwargs):
        # Add extra context to log messages
        if self.extra:
            context = ", ".join(f"{k}={v}" for k, v in self.extra.items())
            msg = f"[{context}] {msg}"
        return msg, kwargs


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with contextual information.
    
    Args:
        name: Logger name
        **context: Additional context to add to log messages
        
    Returns:
        LoggerAdapter with context
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context)


# Initialize logging on module import
logger = setup_logging()

