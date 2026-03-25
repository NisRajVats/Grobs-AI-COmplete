"""
Custom Exceptions Module

Defines application-specific exceptions for consistent error handling
across the GrobsAI Backend.
"""
from typing import Optional, Any, Dict
from fastapi import HTTPException, status


class GrobsAIException(Exception):
    """
    Base exception for all GrobsAI application errors.
    
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# ==================== Authentication Exceptions ====================

class AuthenticationError(GrobsAIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials are invalid."""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class RefreshTokenError(AuthenticationError):
    """Raised when refresh token operations fail."""
    
    def __init__(self, message: str = "Failed to refresh token"):
        super().__init__(message)


# ==================== Authorization Exceptions ====================

class AuthorizationError(GrobsAIException):
    """Raised when user lacks permission."""
    
    def __init__(self, message: str = "Not authorized", details: Optional[Dict] = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user doesn't have required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message)


# ==================== Resource Exceptions ====================

class NotFoundError(GrobsAIException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, resource_id: Optional[Any] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID {resource_id} not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND, {"resource": resource, "id": resource_id})


class AlreadyExistsError(GrobsAIException):
    """Raised when trying to create a duplicate resource."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} '{identifier}' already exists"
        super().__init__(message, status.HTTP_409_CONFLICT, {"resource": resource})


class ResourceConflictError(GrobsAIException):
    """Raised when there's a conflict with the current state of a resource."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


# ==================== Validation Exceptions ====================

class ValidationError(GrobsAIException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class InvalidFileError(ValidationError):
    """Raised when file validation fails."""
    
    def __init__(self, message: str = "Invalid file"):
        super().__init__(message, {"type": "file_error"})


class FileSizeExceededError(InvalidFileError):
    """Raised when file size exceeds limit."""
    
    def __init__(self, max_size_mb: int):
        message = f"File size exceeds maximum allowed size of {max_size_mb}MB"
        super().__init__(message)
        self.details = {"max_size_mb": max_size_mb, "type": "file_size_exceeded"}


class UnsupportedFileTypeError(InvalidFileError):
    """Raised when file type is not supported."""
    
    def __init__(self, file_type: str, allowed_types: list):
        message = f"File type '{file_type}' is not supported. Allowed types: {', '.join(allowed_types)}"
        super().__init__(message)
        self.details = {"file_type": file_type, "allowed_types": allowed_types}


# ==================== Processing Exceptions ====================

class ProcessingError(GrobsAIException):
    """Raised when processing fails (e.g., resume parsing, AI analysis)."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class ParsingError(ProcessingError):
    """Raised when resume/document parsing fails."""
    
    def __init__(self, message: str = "Failed to parse document"):
        super().__init__(message)


class EmbeddingError(ProcessingError):
    """Raised when embedding generation fails."""
    
    def __init__(self, message: str = "Failed to generate embeddings"):
        super().__init__(message)


class AnalysisError(ProcessingError):
    """Raised when AI analysis fails."""
    
    def __init__(self, message: str = "Analysis failed"):
        super().__init__(message)


# ==================== External Service Exceptions ====================

class ExternalServiceError(GrobsAIException):
    """Raised when external service (LLM, storage, etc.) fails."""
    
    def __init__(self, service: str, message: str = "External service error"):
        full_message = f"{service}: {message}"
        super().__init__(full_message, status.HTTP_503_SERVICE_UNAVAILABLE, {"service": service})


class LLMServiceError(ExternalServiceError):
    """Raised when LLM service fails."""
    
    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__("LLM", message)


class StorageServiceError(ExternalServiceError):
    """Raised when storage service fails."""
    
    def __init__(self, message: str = "Storage service unavailable"):
        super().__init__("Storage", message)


class VectorDBError(ExternalServiceError):
    """Raised when vector database operations fail."""
    
    def __init__(self, message: str = "Vector database error"):
        super().__init__("VectorDB", message)


# ==================== Rate Limiting ====================

class RateLimitError(GrobsAIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)
        self.details = {"retry_after": retry_after} if retry_after else {}


# ==================== HTTP Exception Factory ====================

def http_exception_from_grobs_exception(exc: GrobsAIException) -> HTTPException:
    """
    Convert a GrobsAI exception to a FastAPI HTTPException.
    
    Args:
        exc: GrobsAI exception
        
    Returns:
        FastAPI HTTPException
    """
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.to_dict()
    )


# ==================== Exception Handlers ====================

def register_exception_handlers(app):
    """
    Register exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    
    @app.exception_handler(GrobsAIException)
    async def grobs_exception_handler(request: Request, exc: GrobsAIException):
        """Handle all GrobsAI custom exceptions."""
        logger.warning(f"GrobsAI Exception: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )

