"""
Core Module

Contains fundamental infrastructure components:
- config: Configuration management
- database: Database session and engine
- exceptions: Custom exceptions
- logging: Logging configuration
- security: Authentication and authorization
"""
from app.core.config import settings, get_settings, config

__all__ = [
    "settings",
    "get_settings", 
    "config",
]

