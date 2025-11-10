"""
Shared FastAPI Dependencies

Common dependencies that can be injected into multiple endpoints.
"""

from fastapi import Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.utils.database import get_database
from src.api.settings import settings
from src.api.auth.api_key import verify_api_key, get_optional_api_key
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Database dependency - can be used in any endpoint
async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency for database injection.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Usage:
        @router.get("/books")
        async def get_books(db: AsyncIOMotorDatabase = Depends(get_db)):
            books = await db.books.find().to_list(length=10)
            return books
    """
    return get_database()


# Authentication dependency (for protected routes)
async def require_api_key(api_key: str = Depends(verify_api_key)) -> str:
    """
    Require valid API key for endpoint access.
    
    This is an alias for verify_api_key for clearer intent in route definitions.
    
    Args:
        api_key: Validated API key from header
        
    Returns:
        str: Validated API key
        
    Usage:
        @router.get("/protected", dependencies=[Depends(require_api_key)])
        async def protected_endpoint():
            return {"message": "Access granted"}
    """
    return api_key


# Optional authentication dependency
async def optional_api_key(api_key: Optional[str] = Depends(get_optional_api_key)) -> Optional[str]:
    """
    Optional API key validation.
    
    Args:
        api_key: API key if provided and valid, None otherwise
        
    Returns:
        Optional[str]: Validated API key or None
        
    Usage:
        @router.get("/public-or-private")
        async def mixed_endpoint(api_key: Optional[str] = Depends(optional_api_key)):
            if api_key:
                return {"access": "authenticated"}
            return {"access": "public"}
    """
    return api_key


async def common_parameters(
    skip: int = 0,
    limit: int = 100
):
    """
    Common pagination parameters.
    
    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)
        
    Returns:
        dict: Pagination parameters
        
    Note:
        Limit will be validated against settings.max_page_size
    """
    # Validate against max page size
    validated_limit = min(limit, settings.max_page_size)
    
    return {"skip": skip, "limit": validated_limit}
