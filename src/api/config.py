"""
API Configuration Module

Manages all API-related settings using Pydantic BaseSettings.
Settings are loaded from environment variables and .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class APISettings(BaseSettings):
    """
    API Configuration Settings.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    # ==================== Server Configuration ====================
    api_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server"
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port to bind the API server"
    )
    api_title: str = Field(
        default="Books to Scrape API",
        description="API title displayed in documentation"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_description: str = Field(
        default="RESTful API for querying crawled book data",
        description="API description for documentation"
    )
    
    # ==================== Database Configuration ====================
    mongo_uri: str = Field(
        ...,  # Required
        description="MongoDB connection string (reused from crawler)"
    )
    
    # ==================== Security Configuration ====================
    api_keys: str = Field(
        ...,  # Required
        description="Comma-separated API keys in format: hash1:desc1,hash2:desc2"
    )
    
    rate_limit_per_hour: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum requests per hour per API key"
    )
    
    # ==================== CORS Configuration ====================
    allowed_origins: str = Field(
        default="*",
        description="Comma-separated allowed origins or * for all"
    )
    
    # ==================== Pagination Configuration ====================
    default_page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Default number of items per page"
    )
    
    max_page_size: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum allowed items per page"
    )
    
    # ==================== Logging Configuration ====================
    api_log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    log_to_file: bool = Field(
        default=True,
        description="Enable file logging"
    )
    
    log_json_format: bool = Field(
        default=False,
        description="Enable JSON structured logging (recommended for production)"
    )
    
    log_rotation: bool = Field(
        default=True,
        description="Enable log file rotation"
    )
    
    # ==================== Computed Properties ====================
    @property
    def parsed_api_keys(self) -> Dict[str, str]:
        """
        Parse API keys from string format to dictionary.
        
        Returns:
            Dict[str, str]: {key_hash: description}
        """
        keys = {}
        for item in self.api_keys.split(','):
            item = item.strip()
            if ':' in item:
                key, desc = item.split(':', 1)
                keys[key.strip()] = desc.strip()
            else:
                keys[item] = "Default key"
        return keys
    
    @property
    def parsed_allowed_origins(self) -> List[str]:
        """
        Parse allowed origins from string to list.
        
        Returns:
            List[str]: List of allowed origin URLs
        """
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(',')]
    
    # ==================== Validators ====================
    @field_validator('api_log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid logging level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper
    
    @field_validator('default_page_size')
    @classmethod
    def validate_default_page_size(cls, v: int, info) -> int:
        """Ensure default page size doesn't exceed max page size."""
        # Note: max_page_size may not be set yet during validation
        # Will validate in __init__ if needed
        return v
    
    # ==================== Model Configuration ====================
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
        "case_sensitive": False
    }
    
    def __init__(self, **kwargs):
        """Initialize settings and perform cross-field validation."""
        super().__init__(**kwargs)
        
        # Cross-field validation
        if self.default_page_size > self.max_page_size:
            logger.warning(
                f"default_page_size ({self.default_page_size}) exceeds "
                f"max_page_size ({self.max_page_size}). "
                f"Setting default to {self.max_page_size}"
            )
            self.default_page_size = self.max_page_size
        
        # Validate API keys format
        if not self.api_keys:
            raise ValueError("API_KEYS must be configured in .env file")
        
        # Log configuration summary
        logger.info("API Configuration loaded:")
        logger.info(f"  - Server: {self.api_host}:{self.api_port}")
        logger.info(f"  - Title: {self.api_title} v{self.api_version}")
        logger.info(f"  - Rate Limit: {self.rate_limit_per_hour} req/hour")
        logger.info(f"  - API Keys: {len(self.parsed_api_keys)} configured")
        logger.info(f"  - CORS Origins: {len(self.parsed_allowed_origins)}")
        logger.info(f"  - Pagination: {self.default_page_size} default, {self.max_page_size} max")
        logger.info(f"  - Log Level: {self.api_log_level}")


# Global settings instance
# This will be imported throughout the API
settings = APISettings()
