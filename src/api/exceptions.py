"""
Custom Exceptions and Exception Handlers

Defines custom exceptions and registers global exception handlers.
Will be fully implemented in Step 10.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


class BookNotFoundException(Exception):
    """Raised when a book is not found in the database."""
    def __init__(self, book_id: str):
        self.book_id = book_id
        super().__init__(f"Book with ID {book_id} not found")


class InvalidAPIKeyException(Exception):
    """Raised when an invalid API key is provided."""
    pass


class RateLimitExceededException(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


def register_exception_handlers(app: FastAPI):
    """
    Register global exception handlers for the FastAPI app.
    
    Will be fully implemented in Step 10.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    logger.info("Exception handlers registered (placeholder)")
