"""
API Key Authentication

Implements API key validation using X-API-Key header with SHA-256 hashing.
Provides security dependency for protecting endpoints.
"""

from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from src.api.settings import settings
from src.utils.logging import log_authentication
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("api.auth")

# API Key header security scheme
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for authentication. Include in X-API-Key header."
)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        SHA-256 hash of the API key (hex format)
        
    Example:
        >>> hash_api_key("my_secret_key")
        '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key_hash(api_key: str) -> tuple[bool, Optional[str]]:
    """
    Validate API key against configured hashes.
    
    Args:
        api_key: Plain text API key from request
        
    Returns:
        Tuple of (is_valid, key_description)
        - is_valid: True if key is valid
        - key_description: Description of the key if valid, None otherwise
    """
    # Hash the provided key
    key_hash = hash_api_key(api_key)
    
    # Get configured API keys from settings
    valid_keys = settings.parsed_api_keys
    
    # Check if hash matches any configured key
    if key_hash in valid_keys:
        return True, valid_keys[key_hash]
    
    return False, None


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Validate API key from request header.
    
    This dependency should be used on protected endpoints to ensure
    only authenticated requests are processed.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        str: Validated API key (plain text for rate limiting)
        
    Raises:
        HTTPException: 401 if key is missing or invalid
        
    Example:
        @router.get("/protected")
        async def protected_route(api_key: str = Depends(verify_api_key)):
            return {"message": "Access granted"}
    """
    # Check if API key is provided
    if not api_key:
        masked_key = "none"
        log_authentication(logger, success=False, api_key=masked_key, reason="missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Missing API key",
                "message": "Include X-API-Key header in your request",
                "header": "X-API-Key"
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate the API key
    is_valid, key_description = validate_api_key_hash(api_key)
    masked_key = api_key[:8] + "..." if len(api_key) > 8 else api_key
    
    if not is_valid:
        log_authentication(logger, success=False, api_key=masked_key, reason="invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid API key",
                "message": "The provided API key is not valid",
                "hint": "Check your API key or contact the administrator"
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Log successful authentication
    log_authentication(logger, success=True, api_key=masked_key, description=key_description)
    
    # Return the plain text key (needed for rate limiting by key)
    return api_key


async def get_optional_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[str]:
    """
    Optional API key validation for endpoints that support both
    authenticated and unauthenticated access.
    
    Args:
        api_key: API key from X-API-Key header (optional)
        
    Returns:
        Validated API key if provided and valid, None otherwise
        
    Example:
        @router.get("/public-or-private")
        async def mixed_route(api_key: Optional[str] = Depends(get_optional_api_key)):
            if api_key:
                return {"access": "authenticated"}
            return {"access": "public"}
    """
    if not api_key:
        return None
    
    # Validate if provided
    is_valid, key_description = validate_api_key_hash(api_key)
    masked_key = api_key[:8] + "..." if len(api_key) > 8 else api_key
    
    if is_valid:
        log_authentication(logger, success=True, api_key=masked_key, description=key_description, optional=True)
        return api_key
    else:
        log_authentication(logger, success=False, api_key=masked_key, reason="invalid", optional=True)
        return None


def get_api_key_info(api_key: str) -> dict:
    """
    Get information about an API key.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Dictionary with key information:
        - hash: SHA-256 hash of the key
        - valid: Whether the key is valid
        - description: Key description if valid
        
    Example:
        >>> info = get_api_key_info("test_key")
        >>> print(info)
        {
            'hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
            'valid': True,
            'description': 'Test API Key'
        }
    """
    key_hash = hash_api_key(api_key)
    is_valid, description = validate_api_key_hash(api_key)
    
    return {
        "hash": key_hash,
        "valid": is_valid,
        "description": description if is_valid else None
    }


# Helper function to generate new API key hashes (for admin use)
def generate_api_key_hash(plain_key: str, description: str) -> str:
    """
    Generate a formatted API key hash for .env file.
    
    Args:
        plain_key: Plain text API key
        description: Description for the key
        
    Returns:
        Formatted string: "hash:description"
        
    Example:
        >>> generate_api_key_hash("my_secret_key", "Production Key")
        '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8:Production Key'
    """
    key_hash = hash_api_key(plain_key)
    return f"{key_hash}:{description}"

