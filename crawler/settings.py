from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Union

class Settings(BaseSettings):
    mongo_uri: str
    max_concurrency: int = 10
    request_timeout: int = 10
    retry_attempts: int = 5
    request_interval: float = 1.0  # Time between requests in seconds
    user_agent: str = "BooksCrawler/1.0"
    store_html_in_gridfs: bool = True

    @field_validator('max_concurrency')
    def validate_max_concurrency(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_concurrency must be at least 1")
        if v > 20:
            raise ValueError("max_concurrency should not exceed 20 to avoid overwhelming the server")
        return v

    @field_validator('request_timeout')
    def validate_timeout(cls, v: int) -> int:
        if v < 1:
            raise ValueError("request_timeout must be at least 1 second")
        if v > 60:
            raise ValueError("request_timeout should not exceed 60 seconds")
        return v

    @field_validator('retry_attempts')
    def validate_retries(cls, v: int) -> int:
        if v < 1:
            raise ValueError("retry_attempts must be at least 1")
        if v > 10:
            raise ValueError("retry_attempts should not exceed 10")
        return v

    @field_validator('request_interval')
    def validate_request_interval(cls, v: float) -> float:
        if v < 0.1:
            raise ValueError("request_interval must be at least 0.1 seconds")
        if v > 10.0:
            raise ValueError("request_interval should not exceed 10 seconds")
        return v

    class Config:
        env_file = ".env"
