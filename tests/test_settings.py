"""
Unit tests for the settings module.
"""

import os
import pytest
from pathlib import Path
from typing import Dict, Generator
from crawler.settings import Settings as CrawlerSettings
from scheduler.settings import Settings as SchedulerSettings


@pytest.fixture
def env_backup() -> Generator[Dict[str, str], None, None]:
    """Backup and restore environment variables."""
    # Save current environment variables
    keys_to_backup = [
        'MONGODB_URL', 'REPORTS_DIR', 'CRAWL_INTERVAL',
        'MONGO_URI', 'MAX_CONCURRENCY', 'REQUEST_TIMEOUT',
        'RETRY_ATTEMPTS', 'USER_AGENT', 'STORE_HTML_IN_GRIDFS',
        'LOGGING_LEVEL'
    ]
    old_env = {key: os.environ.get(key) for key in keys_to_backup}
    
    yield old_env
    
    # Restore original environment variables
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def scheduler_settings(env_backup: Dict[str, str]) -> SchedulerSettings:
    """Create a SchedulerSettings instance with test values."""
    os.environ.update({
        'MONGODB_URL': 'mongodb://localhost:27017',
        'REPORTS_DIR': './test_reports',
        'CRAWL_INTERVAL': '60',
        'LOGGING_LEVEL': 'DEBUG'
    })
    return SchedulerSettings()


@pytest.fixture
def crawler_settings(env_backup: Dict[str, str]) -> CrawlerSettings:
    """Create a CrawlerSettings instance with test values."""
    os.environ.update({
        'MONGO_URI': 'mongodb://localhost:27017/test_books',
        'MAX_CONCURRENCY': '5',
        'REQUEST_TIMEOUT': '5',
        'RETRY_ATTEMPTS': '3',
        'USER_AGENT': 'TestCrawler/1.0',
        'STORE_HTML_IN_GRIDFS': 'true'
    })
    return CrawlerSettings()


def test_scheduler_settings_from_env(scheduler_settings: SchedulerSettings) -> None:
    """Test loading scheduler settings from environment variables."""
    assert scheduler_settings.mongodb_url == 'mongodb://localhost:27017'
    assert scheduler_settings.reports_dir == './test_reports'
    assert scheduler_settings.crawl_interval == 60
    assert scheduler_settings.logging_level == 'DEBUG'


def test_crawler_settings_from_env(crawler_settings: CrawlerSettings) -> None:
    """Test loading crawler settings from environment variables."""
    assert crawler_settings.mongo_uri == 'mongodb://localhost:27017/test_books'
    assert crawler_settings.max_concurrency == 5
    assert crawler_settings.request_timeout == 5
    assert crawler_settings.retry_attempts == 3
    assert crawler_settings.user_agent == 'TestCrawler/1.0'
    assert crawler_settings.store_html_in_gridfs is True


def test_scheduler_settings_defaults(env_backup: Dict[str, str]) -> None:
    """Test default scheduler settings when environment variables are not set."""
    settings = SchedulerSettings()
    assert settings.mongodb_url == 'mongodb://localhost:27017'
    assert settings.reports_dir == './reports'
    assert settings.crawl_interval == 3600
    assert settings.logging_level == 'INFO'


def test_crawler_settings_defaults(env_backup: Dict[str, str]) -> None:
    """Test default crawler settings when environment variables are not set."""
    settings = CrawlerSettings()
    assert settings.mongo_uri == 'mongodb://localhost:27017/books'
    assert settings.max_concurrency == 10
    assert settings.request_timeout == 10
    assert settings.retry_attempts == 5
    assert settings.request_interval == 1.0
    assert settings.store_html_in_gridfs is True


def test_scheduler_invalid_crawl_interval(env_backup: Dict[str, str]) -> None:
    """Test validation of invalid scheduler crawl interval."""
    os.environ['CRAWL_INTERVAL'] = '-1'
    with pytest.raises(ValueError, match='crawl_interval must be positive'):
        SchedulerSettings()


def test_crawler_invalid_concurrency(env_backup: Dict[str, str]) -> None:
    """Test validation of invalid crawler concurrency settings."""
    os.environ['MAX_CONCURRENCY'] = '21'
    with pytest.raises(ValueError, match='max_concurrency should not exceed 20'):
        CrawlerSettings()


def test_scheduler_invalid_logging_level(env_backup: Dict[str, str]) -> None:
    """Test validation of invalid logging level."""
    os.environ['LOGGING_LEVEL'] = 'INVALID'
    with pytest.raises(ValueError) as exc_info:
        SchedulerSettings()
    assert "Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'" in str(exc_info.value)


def test_create_reports_dir(tmp_path: Path, env_backup: Dict[str, str]) -> None:
    """Test creation of reports directory."""
    reports_dir = tmp_path / 'test_reports'
    os.environ['REPORTS_DIR'] = str(reports_dir)
    
    # Create settings (this should create the directory)
    settings = SchedulerSettings()
    
    # Access the reports_dir property to trigger directory creation
    _ = settings.reports_dir
    
    assert reports_dir.exists(), f"Reports directory {reports_dir} was not created"
    assert reports_dir.is_dir(), f"{reports_dir} is not a directory"
    assert reports_dir.is_absolute(), f"{reports_dir} is not an absolute path"