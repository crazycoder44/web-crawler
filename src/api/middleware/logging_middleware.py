"""
Logging Middleware

Structured logging middleware for API requests and responses.
Logs request details, response status, and execution time.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import json
from typing import Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Logs:
    - Request method, path, query params
    - Client IP address
    - API key (masked)
    - Response status code
    - Execution time
    - Request/response sizes
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the logging middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.logger = logging.getLogger("api.requests")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/endpoint handler
            
        Returns:
            Response: The HTTP response
        """
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = self._get_client_ip(request)
        api_key = self._get_masked_api_key(request)
        
        # Log request
        self.logger.info(
            self._format_request_log(
                method=method,
                path=path,
                query_params=query_params,
                client_ip=client_ip,
                api_key=api_key
            )
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                self._format_response_log(
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    execution_time=execution_time,
                    client_ip=client_ip
                )
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = str(id(request))
            response.headers["X-Execution-Time"] = f"{execution_time:.3f}s"
            
            return response
            
        except Exception as e:
            # Log exception
            execution_time = time.time() - start_time
            self.logger.error(
                self._format_error_log(
                    method=method,
                    path=path,
                    error=str(e),
                    execution_time=execution_time,
                    client_ip=client_ip
                )
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Args:
            request: The HTTP request
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_masked_api_key(self, request: Request) -> str:
        """
        Extract and mask API key from request.
        
        Args:
            request: The HTTP request
            
        Returns:
            str: Masked API key (shows first 8 chars)
        """
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return "none"
        
        # Show first 8 characters only
        if len(api_key) > 8:
            return f"{api_key[:8]}..."
        return api_key
    
    def _format_request_log(
        self,
        method: str,
        path: str,
        query_params: dict,
        client_ip: str,
        api_key: str
    ) -> str:
        """
        Format request log message.
        
        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            client_ip: Client IP address
            api_key: Masked API key
            
        Returns:
            str: Formatted log message
        """
        log_data = {
            "event": "request_started",
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "api_key": api_key,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if query_params:
            log_data["query_params"] = query_params
        
        return json.dumps(log_data)
    
    def _format_response_log(
        self,
        method: str,
        path: str,
        status_code: int,
        execution_time: float,
        client_ip: str
    ) -> str:
        """
        Format response log message.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            execution_time: Request execution time
            client_ip: Client IP address
            
        Returns:
            str: Formatted log message
        """
        log_data = {
            "event": "request_completed",
            "method": method,
            "path": path,
            "status_code": status_code,
            "execution_time": f"{execution_time:.3f}s",
            "client_ip": client_ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return json.dumps(log_data)
    
    def _format_error_log(
        self,
        method: str,
        path: str,
        error: str,
        execution_time: float,
        client_ip: str
    ) -> str:
        """
        Format error log message.
        
        Args:
            method: HTTP method
            path: Request path
            error: Error message
            execution_time: Request execution time
            client_ip: Client IP address
            
        Returns:
            str: Formatted log message
        """
        log_data = {
            "event": "request_error",
            "method": method,
            "path": path,
            "error": error,
            "execution_time": f"{execution_time:.3f}s",
            "client_ip": client_ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return json.dumps(log_data)


def setup_logging_middleware(app):
    """
    Set up logging middleware for the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware configured")
