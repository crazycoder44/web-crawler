"""
Global Exception Handlers

Provides consistent error responses across the API.
Handles common HTTP exceptions and unexpected errors with proper logging.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import logging
from datetime import datetime
from typing import Union

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTP exceptions (404, 401, 403, etc.).
    
    Provides consistent error response format with proper logging.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception raised
        
    Returns:
        JSONResponse with error details
    """
    # Log the error with context
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method} | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # Determine error category
    error_type = "error"
    if exc.status_code == 401:
        error_type = "authentication_error"
    elif exc.status_code == 403:
        error_type = "authorization_error"
    elif exc.status_code == 404:
        error_type = "not_found"
    elif exc.status_code == 422:
        error_type = "validation_error"
    elif exc.status_code == 429:
        error_type = "rate_limit_exceeded"
    
    # Build error response
    error_response = {
        "status": error_type,
        "message": str(exc.detail),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": request.url.path
    }
    
    # Add retry information for rate limiting
    if exc.status_code == 429 and hasattr(exc, "headers"):
        retry_after = exc.headers.get("Retry-After")
        if retry_after:
            error_response["retry_after_seconds"] = int(retry_after)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors (422).
    
    Formats validation errors in a user-friendly way with field-level details.
    
    Args:
        request: FastAPI request object
        exc: Validation exception from Pydantic
        
    Returns:
        JSONResponse with detailed validation errors
    """
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log validation errors
    logger.warning(
        f"Validation error: {len(errors)} field(s) invalid | "
        f"Path: {request.url.path} | "
        f"Method: {request.method} | "
        f"Errors: {errors[:3]}"  # Log first 3 errors
    )
    
    # Build error response
    error_response = {
        "status": "validation_error",
        "message": f"Request validation failed: {len(errors)} error(s)",
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": request.url.path
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic ValidationError (internal model validation).
    
    Args:
        request: FastAPI request object
        exc: Pydantic ValidationError
        
    Returns:
        JSONResponse with validation error details
    """
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.error(
        f"Pydantic validation error: {len(errors)} field(s) | "
        f"Path: {request.url.path} | "
        f"Errors: {errors}"
    )
    
    error_response = {
        "status": "validation_error",
        "message": "Data validation failed",
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": request.url.path
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions (500 Internal Server Error).
    
    Logs full stack trace for debugging while returning safe error message to client.
    
    Args:
        request: FastAPI request object
        exc: Any unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    # Log full exception with stack trace
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method} | "
        f"Client: {request.client.host if request.client else 'unknown'}",
        exc_info=True
    )
    
    # Build safe error response (don't expose internal details)
    error_response = {
        "status": "internal_error",
        "message": "An internal server error occurred. Please try again later.",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": request.url.path
    }
    
    # In development, include exception details (disabled in production)
    # Uncomment for debugging:
    # error_response["debug"] = {
    #     "type": type(exc).__name__,
    #     "detail": str(exc)
    # }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle database-related exceptions.
    
    Catches MongoDB connection errors and query failures.
    
    Args:
        request: FastAPI request object
        exc: Database exception
        
    Returns:
        JSONResponse with database error details
    """
    logger.error(
        f"Database error: {type(exc).__name__}: {str(exc)} | "
        f"Path: {request.url.path}",
        exc_info=True
    )
    
    error_response = {
        "status": "database_error",
        "message": "A database error occurred. Please try again later.",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": request.url.path
    }
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # HTTP exceptions (404, 401, 403, etc.)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Request validation errors (422)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Database exceptions
    from pymongo.errors import PyMongoError
    app.add_exception_handler(PyMongoError, database_exception_handler)
    
    # Catch-all for unexpected exceptions (500)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ Exception handlers registered")
