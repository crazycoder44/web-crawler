"""
Rate Limiting Middleware

Implements sliding window rate limiting for API requests per API key.
Uses in-memory storage with automatic cleanup of expired entries.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Deque
from src.api.settings import settings
from src.api.auth.api_key import hash_api_key
from src.utils.logging import log_rate_limit
import logging
import asyncio

logger = logging.getLogger("api.rate_limiter")


class RateLimitStore:
    """
    In-memory storage for rate limit tracking using sliding window.
    
    Stores timestamps of requests per API key to calculate rate limits
    within a rolling time window.
    """
    
    def __init__(self):
        """Initialize the rate limit store."""
        self._requests: Dict[str, Deque[datetime]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
    
    async def record_request(self, key_identifier: str) -> None:
        """
        Record a request timestamp for the given API key.
        
        Args:
            key_identifier: Hashed API key identifier
        """
        async with self._lock:
            now = datetime.utcnow()
            
            if key_identifier not in self._requests:
                self._requests[key_identifier] = deque()
            
            self._requests[key_identifier].append(now)
    
    async def get_request_count(self, key_identifier: str, window_seconds: int) -> int:
        """
        Get the number of requests within the time window.
        
        Args:
            key_identifier: Hashed API key identifier
            window_seconds: Time window in seconds
            
        Returns:
            Number of requests within the window
        """
        async with self._lock:
            if key_identifier not in self._requests:
                return 0
            
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Remove old requests outside the window
            requests = self._requests[key_identifier]
            while requests and requests[0] < cutoff:
                requests.popleft()
            
            return len(requests)
    
    async def cleanup_expired(self, window_seconds: int) -> None:
        """
        Clean up expired request records to save memory.
        
        Args:
            window_seconds: Time window in seconds
        """
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            
            keys_to_delete = []
            
            for key_identifier, requests in self._requests.items():
                # Remove old requests
                while requests and requests[0] < cutoff:
                    requests.popleft()
                
                # If no requests left, mark for deletion
                if not requests:
                    keys_to_delete.append(key_identifier)
            
            # Delete empty entries
            for key_identifier in keys_to_delete:
                del self._requests[key_identifier]
            
            if keys_to_delete:
                logger.debug(f"Cleaned up {len(keys_to_delete)} expired rate limit entries")
    
    async def get_stats(self) -> dict:
        """
        Get statistics about the rate limit store.
        
        Returns:
            Dictionary with stats
        """
        async with self._lock:
            total_requests = sum(len(requests) for requests in self._requests.values())
            return {
                "tracked_keys": len(self._requests),
                "total_requests": total_requests
            }


# Global rate limit store
rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce sliding window rate limiting on API requests.
    
    Rate limits are enforced per API key based on the configured limit
    (default: 100 requests per hour). Returns 429 when limit is exceeded.
    
    Features:
    - Sliding window algorithm for accurate rate limiting
    - Per-API-key tracking
    - Automatic cleanup of expired entries
    - Rate limit headers in all responses
    - Detailed 429 error responses with Retry-After
    """
    
    def __init__(self, app, rate_limit_per_hour: int = None):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            rate_limit_per_hour: Requests allowed per hour (default: from settings)
        """
        super().__init__(app)
        self.rate_limit = rate_limit_per_hour or settings.rate_limit_per_hour
        self.window_seconds = 3600  # 1 hour in seconds
        
        # Paths that are exempt from rate limiting
        self.exempt_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        logger.info(f"Rate limiting enabled: {self.rate_limit} requests per hour")
    
    def is_exempt(self, path: str) -> bool:
        """
        Check if a path is exempt from rate limiting.
        
        Args:
            path: Request path
            
        Returns:
            True if exempt, False otherwise
        """
        return path in self.exempt_paths
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response with rate limit headers
        """
        # Check if path is exempt
        if self.is_exempt(request.url.path):
            response = await call_next(request)
            return response
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        # If no API key, let the request through (auth will handle it)
        if not api_key:
            response = await call_next(request)
            # Add rate limit headers showing unauthenticated status
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
            response.headers["X-RateLimit-Remaining"] = "N/A"
            response.headers["X-RateLimit-Reset"] = "N/A"
            return response
        
        # Hash the API key for storage (privacy)
        key_identifier = hash_api_key(api_key)
        
        # Get current request count
        current_count = await rate_limit_store.get_request_count(
            key_identifier,
            self.window_seconds
        )
        
        # Calculate remaining requests
        remaining = max(0, self.rate_limit - current_count)
        
        # Check if rate limit exceeded
        if current_count >= self.rate_limit:
            # Calculate reset time
            now = datetime.utcnow()
            reset_time = now + timedelta(seconds=self.window_seconds)
            retry_after = self.window_seconds  # In seconds
            
            # Log rate limit exceeded
            masked_key = api_key[:8] + "..." if len(api_key) > 8 else api_key
            log_rate_limit(
                logger,
                api_key=masked_key,
                current=current_count,
                limit=self.rate_limit,
                path=request.url.path
            )
            
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"You have exceeded the rate limit of {self.rate_limit} requests per hour",
                    "limit": self.rate_limit,
                    "window": "1 hour",
                    "retry_after_seconds": retry_after,
                    "reset_at": reset_time.isoformat() + "Z"
                },
                headers={
                    "X-RateLimit-Limit": str(self.rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time.timestamp())),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Record this request
        await rate_limit_store.record_request(key_identifier)
        
        # Update remaining count after recording
        remaining = max(0, remaining - 1)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        now = datetime.utcnow()
        reset_time = now + timedelta(seconds=self.window_seconds)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
        
        return response


async def start_cleanup_task():
    """
    Start background task to clean up expired rate limit entries.
    
    This should be called on application startup.
    """
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await rate_limit_store.cleanup_expired(3600)
            except asyncio.CancelledError:
                logger.info("Rate limit cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")
    
    task = asyncio.create_task(cleanup_loop())
    logger.info("Rate limit cleanup task started")
    return task


async def get_rate_limit_stats() -> dict:
    """
    Get current rate limit statistics.
    
    Returns:
        Dictionary with rate limit stats
    """
    return await rate_limit_store.get_stats()
