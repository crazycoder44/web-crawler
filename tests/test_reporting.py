"""
Unit tests for the report generation system.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
from pathlib import Path
from bson import ObjectId

from scheduler.reporting import ChangeReporter
from scheduler.models import ChangeRecord

@pytest_asyncio.fixture
async def reporter():
    """Create a ChangeReporter instance with mocked database."""
    reporter = ChangeReporter()
    
    # Create mock store
    mock_store = AsyncMock()
    mock_store.books = AsyncMock()
    
    # Configure mock responses
    async def mock_find_one(*args, **kwargs):
        return {
            '_id': ObjectId("507f1f77bcf86cd799439011"),
            'title': 'Test Book',
            'price': 19.99
        }
    mock_store.books.find_one = mock_find_one
    
    async def mock_record_change(*args, **kwargs):
        return "607f1f77bcf86cd799439012"
    mock_store.record_change = mock_record_change
    
    # Set the mock store
    reporter.store = mock_store
    
    return reporter

@pytest.mark.asyncio
async def test_record_change(reporter):
    """Test recording a single change."""
    book_id = "507f1f77bcf86cd799439011"
    changes = {
        'price': {
            'old': '19.99',
            'new': '24.99'
        }
    }
    
    # Mock store's record_change method
    record_called = False
    async def mock_record(*args, **kwargs):
        nonlocal record_called
        record_called = True
        return "607f1f77bcf86cd799439012"
    reporter.store.record_change = mock_record
    
    # Record change
    change_id = await reporter.record_change(book_id, changes)
    
    assert change_id == "607f1f77bcf86cd799439012"
    assert record_called

@pytest.mark.asyncio
async def test_generate_daily_report(reporter):
    """Test generating a daily summary report."""
    # Mock the store's get_recent_changes method
    today = datetime.utcnow()
    mock_changes = [
        {
            'book_id': ObjectId(),
            'changes': {
                'price': {
                    'old': '19.99',
                    'new': '24.99'
                }
            },
            'timestamp': today
        }
    ]
    
    async def mock_get_recent_changes(*args, **kwargs):
        return mock_changes
    reporter.store.get_recent_changes = mock_get_recent_changes
    
    # Mock get_crawl_metrics
    async def mock_get_metrics(*args, **kwargs):
        return {
            'total_books': 100,
            'error_rate': 0.5,
            'categories': ['Fiction', 'Non-Fiction'],
            'avg_response_time': [{'avg_time': 0.5}]
        }
    reporter.store.get_crawl_metrics = mock_get_metrics
    
    report = await reporter.generate_daily_report(today)
    
    assert report['total_books'] == 100
    assert report['updated_books'] == 1
    assert 'price' in report['changes_by_type']

@pytest.mark.asyncio
async def test_save_report_files(reporter, tmp_path):
    """Test saving report files in both JSON and CSV formats."""
    # Set up test report data
    report = {
        'date': '2025-11-08',
        'total_changes': 5,
        'changes_by_type': {
            'price': {
                'count': 3,
                'details': [
                    {
                        'book_title': 'Test Book',
                        'old_value': '19.99',
                        'new_value': '24.99',
                        'timestamp': datetime.utcnow()
                    }
                ]
            }
        }
    }
    
    # Set reports directory to temporary path
    reporter.reports_dir = tmp_path
    
    # Save report files
    await reporter._save_report_files(report, datetime.utcnow())
    
    # Check JSON file
    json_file = list(tmp_path.glob('change_report_*.json'))[0]
    assert json_file.exists()
    
    # Check CSV file
    csv_file = list(tmp_path.glob('change_report_*.csv'))[0]
    assert csv_file.exists()

@pytest.mark.asyncio
async def test_change_statistics(reporter):
    """Test getting change statistics over a period."""
    # Mock get_recent_changes to return mock changes
    period_start = datetime.utcnow() - timedelta(days=2)
    period_end = datetime.utcnow()
    mock_changes = [
        {
            'book_id': ObjectId(),
            'changes': {
                'price': {
                    'old': '19.99',
                    'new': '24.99'
                }
            },
            'timestamp': period_start + timedelta(hours=1)
        },
        {
            'book_id': ObjectId(),
            'changes': {
                'price': {
                    'old': '24.99',
                    'new': '29.99'
                }
            },
            'timestamp': period_start + timedelta(days=1)
        }
    ]
    
    async def mock_get_recent_changes(*args, **kwargs):
        return mock_changes
    reporter.store.get_recent_changes = mock_get_recent_changes
    
    stats = await reporter.get_change_statistics(
        start_date=period_start,
        end_date=period_end
    )
    
    assert stats['period_start'] == period_start.date().isoformat()
    assert stats['period_end'] == period_end.date().isoformat()
    assert len(stats['changes']) == 2
    assert stats['total_changes'] == 2
    assert stats['changes_by_type']['price'] == 2

@pytest.mark.asyncio
async def test_significant_change_detection(reporter):
    """Test detection of significant changes."""
    # Test price change > 20%
    price_change = {
        'field': 'price',
        'old_value': '100.00',
        'new_value': '150.00'
    }
    assert reporter._is_significant_change(price_change) == True
    
    # Test availability change
    availability_change = {
        'field': 'availability',
        'old_value': 'in_stock',
        'new_value': 'out_of_stock'
    }
    assert reporter._is_significant_change(availability_change) == True
    
    # Test non-significant change
    small_price_change = {
        'field': 'price',
        'old_value': '100.00',
        'new_value': '110.00'
    }
    assert reporter._is_significant_change(small_price_change) == False