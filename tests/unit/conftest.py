"""
Pytest Configuration for Unit Tests

Provides fixtures and configuration for unit testing.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_book_data():
    """Sample book data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "source_url": "http://books.toscrape.com/catalogue/test-book_123/index.html",
        "title": "Test Book",
        "price_excl_tax": 20.50,
        "price_incl_tax": 24.60,
        "availability": "In stock (5 available)",
        "num_reviews": 3,
        "rating": 4,
        "category": "Fiction",
        "description": "A test book description",
        "crawl_timestamp": "2025-11-10T00:00:00"
    }


@pytest.fixture
def sample_change_data():
    """Sample change record data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439012",
        "book_id": "507f1f77bcf86cd799439011",
        "timestamp": "2025-11-10T01:00:00",
        "change_type": "update",
        "field_changed": "price_incl_tax",
        "old_value": 24.60,
        "new_value": 22.40
    }


@pytest.fixture
def sample_pagination_data():
    """Sample pagination data for testing."""
    return {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5,
        "has_next": True,
        "has_prev": False
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from unittest.mock import Mock
    
    settings = Mock()
    settings.api_host = "0.0.0.0"
    settings.api_port = 8000
    settings.api_title = "Test API"
    settings.api_version = "1.0.0"
    settings.mongo_uri = "mongodb://localhost:27017/test_db"
    settings.api_log_level = "INFO"
    settings.rate_limit_per_hour = 100
    settings.default_page_size = 20
    settings.max_page_size = 100
    settings.parsed_api_keys = {
        "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key",
        "46d74f2e17ca9220713571e83c870725adf4213f952748f827c9804a38864dc3": "admin_key"
    }
    settings.parsed_allowed_origins = ["*"]
    
    return settings
