"""
Enhanced Logging Configuration

Provides structured logging setup with multiple handlers, formatters,
and log rotation for production use.
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs log records as JSON for easy parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            str: JSON-formatted log message
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output (development).
    
    Adds colors to log levels for better readability.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            str: Colored log message
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False,
    enable_rotation: bool = True
) -> None:
    """
    Configure application logging with multiple handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_json: Enable JSON structured logging
        enable_rotation: Enable log file rotation
    """
    # Create logs directory
    if log_dir is None:
        log_dir = Path("logs")
    
    log_dir.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console Handler (colored for development)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if enable_json:
            console_formatter = StructuredFormatter()
        else:
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File Handler (all logs)
    if enable_file:
        log_file = log_dir / "api.log"
        
        if enable_rotation:
            # Rotating file handler (10 MB per file, keep 10 files)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=10,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(logging.DEBUG)
        
        if enable_json:
            file_formatter = StructuredFormatter()
        else:
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Error File Handler (errors and critical only)
    if enable_file:
        error_log_file = log_dir / "error.log"
        
        if enable_rotation:
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
        else:
            error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        
        error_handler.setLevel(logging.ERROR)
        
        if enable_json:
            error_formatter = StructuredFormatter()
        else:
            error_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
                    'File: %(pathname)s:%(lineno)d\n'
                    'Function: %(funcName)s\n'
                    '%(message)s\n',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    # Set custom levels for API components
    logging.getLogger("api.requests").setLevel(logging.INFO)
    logging.getLogger("api.database").setLevel(logging.INFO)
    logging.getLogger("api.auth").setLevel(logging.INFO)
    logging.getLogger("api.rate_limiter").setLevel(logging.INFO)
    
    root_logger.info(f"Logging configured: level={log_level}, dir={log_dir}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding extra data to log records.
    
    Usage:
        with LogContext(user_id="123", action="create"):
            logger.info("User action performed")
    """
    
    def __init__(self, **kwargs):
        """
        Initialize log context with extra data.
        
        Args:
            **kwargs: Extra data to add to log records
        """
        self.extra_data = kwargs
        self.old_factory = None
    
    def __enter__(self):
        """Enter the context and modify log record factory."""
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_data = self.extra_data
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore log record factory."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Convenience functions for structured logging
def log_request(logger: logging.Logger, method: str, path: str, **kwargs):
    """
    Log an API request with structured data.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        **kwargs: Additional data (client_ip, api_key, etc.)
    """
    with LogContext(event="request", method=method, path=path, **kwargs):
        logger.info(f"{method} {path}")


def log_response(logger: logging.Logger, method: str, path: str, status: int, time: float, **kwargs):
    """
    Log an API response with structured data.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status: HTTP status code
        time: Execution time
        **kwargs: Additional data
    """
    with LogContext(event="response", method=method, path=path, status=status, execution_time=time, **kwargs):
        logger.info(f"{method} {path} - {status} ({time:.3f}s)")


def log_database_operation(logger: logging.Logger, operation: str, collection: str, **kwargs):
    """
    Log a database operation with structured data.
    
    Args:
        logger: Logger instance
        operation: Operation type (find, insert, update, delete)
        collection: Collection name
        **kwargs: Additional data (query, count, etc.)
    """
    with LogContext(event="database", operation=operation, collection=collection, **kwargs):
        logger.info(f"DB {operation} on {collection}")


def log_rate_limit(logger: logging.Logger, api_key: str, current: int, limit: int, **kwargs):
    """
    Log a rate limit event with structured data.
    
    Args:
        logger: Logger instance
        api_key: Masked API key
        current: Current request count
        limit: Rate limit
        **kwargs: Additional data
    """
    with LogContext(event="rate_limit", api_key=api_key, current=current, limit=limit, **kwargs):
        logger.warning(f"Rate limit: {current}/{limit} for {api_key}")


def log_authentication(logger: logging.Logger, success: bool, api_key: str, **kwargs):
    """
    Log an authentication attempt with structured data.
    
    Args:
        logger: Logger instance
        success: Whether authentication succeeded
        api_key: Masked API key
        **kwargs: Additional data
    """
    event = "auth_success" if success else "auth_failure"
    with LogContext(event=event, api_key=api_key, **kwargs):
        if success:
            logger.info(f"Authentication successful: {api_key}")
        else:
            logger.warning(f"Authentication failed: {api_key}")
