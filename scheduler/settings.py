# scheduler/settings.py

"""
Configuration settings for the scheduler module.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from pathlib import Path
from typing import Optional, Literal


class Settings(BaseSettings):
    """Settings for the scheduler module."""
    model_config = ConfigDict(env_file='.env', extra='allow')

    mongodb_url: str = 'mongodb://localhost:27017'
    reports_dir: str = './reports'
    crawl_interval: int = 3600  # Default: 1 hour in seconds
    logging_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_reports_dir()
    
    @field_validator('crawl_interval')
    def validate_interval(cls, v: int) -> int:
        """Validate crawl interval."""
        if v <= 0:
            raise ValueError('crawl_interval must be positive')
        return v

    @field_validator('logging_level')
    def validate_logging_level(cls, v: str) -> str:
        """Validate logging level."""
        return v.upper()

    def _create_reports_dir(self) -> None:
        """Create the reports directory if it doesn't exist."""
        reports_path = Path(self.reports_dir)
        reports_path.mkdir(parents=True, exist_ok=True)


# Create a global instance
settings = Settings()
settings._create_reports_dir()