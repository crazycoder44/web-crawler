"""
Unit tests for the scheduler change detection functionality.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId

from src.scheduler.change_tracker import BookChangeTracker
from src.scheduler.models import BookChange, DailyChangeReport
from src.crawler.models import Book
from pydantic import HttpUrl

@pytest_asyncio.fixture(scope="function")
async def change_tracker():
    """Create a BookChangeTracker instance with mocked database."""
    tracker = BookChangeTracker()
    
    # Mock the store's methods
    mock_store = Mock()
    
    # Make store methods awaitable
    async def mock_get_recent_changes(*args, **kwargs):
        return []
        
    async def mock_get_crawl_metrics(*args, **kwargs):
        return {
            'total_books': 100,
            'error_rate': 0.5,
            'categories': ['Fiction', 'Non-Fiction'],
            'avg_response_time': [{'avg_time': 0.5}]
        }
        
    async def mock_consolidate_changes(*args, **kwargs):
        return True
        
    async def mock_record_change(*args, **kwargs):
        return True
        
    # Attach mock methods
    mock_store.get_recent_changes = mock_get_recent_changes
    mock_store.get_crawl_metrics = mock_get_crawl_metrics
    mock_store.consolidate_changes = mock_consolidate_changes
    mock_store.record_change = mock_record_change
    
    # Set mocked store
    tracker.store = mock_store
    
    return tracker

@pytest.mark.asyncio
async def test_detect_book_changes():
    """Test detecting changes between old and new book data."""
    now = datetime.utcnow()
    test_id = ObjectId()
    
    book = Book(
        id=str(test_id),
        title='Test Book',
        price=19.99,
        availability='in_stock',
        source_url=HttpUrl('http://example.com/book1'),
        fingerprint='test_fp',
        crawl_timestamp=now,
        status='ok'
    )
    
    # Mock store's find_content_changes
    mock_store = Mock()
    async def mock_find_changes(*args, **kwargs):
        return {
            'price': {'old': 19.99, 'new': 24.99},
            'availability': {'old': 'in_stock', 'new': 'out_of_stock'}
        }
    mock_store.find_content_changes = mock_find_changes
    
    # Create tracker with mocked store
    tracker = BookChangeTracker()
    tracker.store = mock_store
    
    # Process update
    change = await tracker.process_book_update(book, "<html>mock html</html>")
    
    assert change is not None
    assert change.changes['price'] == {'old': 19.99, 'new': 24.99}
    assert change.changes['availability'] == {'old': 'in_stock', 'new': 'out_of_stock'}

@pytest.mark.asyncio
async def test_get_daily_changes(change_tracker):
    """Test getting daily changes report."""
    today = datetime.utcnow()
    
    # Mock change records
    mock_changes = [
        {
            'book_id': ObjectId(),
            'changes': {'price': {'old': 24.99, 'new': 29.99}},
            'timestamp': today
        },
        {
            'book_id': ObjectId(),
            'changes': {'availability': {'old': 'in_stock', 'new': 'out_of_stock'}},
            'timestamp': today
        }
    ]
    
    # Override the mock get_recent_changes
    async def mock_get_recent_changes(*args, **kwargs):
        return mock_changes
    change_tracker.store.get_recent_changes = mock_get_recent_changes
    
    # Get daily changes
    report = await change_tracker.get_daily_changes(today)
    
    assert isinstance(report, DailyChangeReport)
    assert report.total_books == 100  # From mock metrics
    assert report.updated_books == 2  # From mock changes
    assert 'price' in report.changes_by_type
    assert 'availability' in report.changes_by_type

@pytest.mark.asyncio
async def test_consolidate_old_changes(change_tracker):
    """Test consolidating old change records."""
    consolidate_called = False
    
    # Override consolidate_changes mock to track call
    async def mock_consolidate(*args, **kwargs):
        nonlocal consolidate_called
        consolidate_called = True
        return True
        
    change_tracker.store.consolidate_changes = mock_consolidate
    
    # Consolidate changes
    await change_tracker.consolidate_old_changes(days_threshold=30)
    
    # Verify consolidation was called
    assert consolidate_called

@pytest.mark.asyncio
async def test_change_detection_empty_changes():
    """Test change detection with no changes."""
    from src.crawler.models import Book
    from pydantic import HttpUrl
    
    now = datetime.utcnow()
    book = Book(
        title='Test Book',
        price=19.99,
        availability='in_stock',
        source_url=HttpUrl('http://example.com/book1'),
        fingerprint='test_fp',
        crawl_timestamp=now
    )
    
    # Mock store to return no changes
    mock_store = Mock()
    async def mock_find_changes(*args, **kwargs):
        return {}
    mock_store.find_content_changes = mock_find_changes
    
    # Create tracker with mocked store
    tracker = BookChangeTracker()
    tracker.store = mock_store
    
    # Process update
    change = await tracker.process_book_update(book, "<html>mock html</html>")
    
    # Should return None when no changes
    assert change is None

@pytest.mark.asyncio
async def test_change_detection_new_fields():
    """Test change detection with new fields added."""
    from src.crawler.models import Book
    from pydantic import HttpUrl
    
    now = datetime.utcnow()
    book = Book(
        title='Test Book',
        price=19.99,
        availability='in_stock',  # New field
        source_url=HttpUrl('http://example.com/book1'),
        fingerprint='test_fp',
        crawl_timestamp=now
    )
    
    # Mock store to return changes including new field
    mock_store = Mock()
    async def mock_find_changes(*args, **kwargs):
        return {
            'availability': {'old': None, 'new': 'in_stock'}
        }
    mock_store.find_content_changes = mock_find_changes
    
    # Create tracker with mocked store
    tracker = BookChangeTracker()
    tracker.store = mock_store
    
    # Process update
    change = await tracker.process_book_update(book, "<html>mock html</html>")
    
    assert change is not None
    assert len(change.changes) == 1
    assert change.changes['availability'] == {'old': None, 'new': 'in_stock'}