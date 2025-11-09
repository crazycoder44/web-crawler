"""
Unit tests for the scheduler functionality.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.operations import IndexModel

from scheduler.scheduler import BookScheduler
from scheduler.jobs import SchedulerJobs
from crawler.store import MongoStore

@pytest_asyncio.fixture
async def store():
    """Create a mocked store instance."""
    mock_store = AsyncMock(spec=MongoStore)
    mock_store.record_scheduler_run = AsyncMock()
    mock_store.get_last_successful_run = AsyncMock(return_value=None)
    mock_store.get_crawl_metrics = AsyncMock(return_value={'success_rate': 0.98, 'response_time': 150})
    mock_store.cleanup_old_snapshots = AsyncMock()
    mock_store.remove_orphaned_snapshots = AsyncMock(return_value=5)
    return mock_store

@pytest_asyncio.fixture
async def scheduler(store):
    """Create a BookScheduler instance with mocked components."""
    scheduler = BookScheduler()
    scheduler.jobs.store = store
    scheduler.jobs.change_tracker = AsyncMock()
    scheduler.jobs.reporter = AsyncMock()
    return scheduler

@pytest_asyncio.fixture
async def scheduler_jobs(store):
    """Create a SchedulerJobs instance with mocked components."""
    jobs = SchedulerJobs()
    jobs.store = store
    jobs.change_tracker = AsyncMock()
    jobs.reporter = AsyncMock()
    jobs.check_database_health = AsyncMock(return_value={'status': 'connected'})
    jobs.get_recent_job_stats = AsyncMock(return_value={'full_site_scan': {'status': 'healthy'}})
    return jobs

@pytest.mark.asyncio
async def test_scheduler_initialization(scheduler):
    """Test scheduler initialization and job configuration."""
    # Verify jobs are configured
    jobs = scheduler.scheduler.get_jobs()
    job_ids = [job.id for job in jobs]
    
    assert 'full_site_scan' in job_ids
    assert 'change_detection' in job_ids
    assert 'maintenance' in job_ids
    assert 'health_check' in job_ids

@pytest.mark.asyncio
async def test_scheduler_job_error_handling(scheduler):
    """Test scheduler error handling for failed jobs."""
    error_event = Mock()
    error_event.job_id = 'test_job'
    error_event.exception = Exception('Test error')
    
    # Create a fixture timestamp for consistent testing
    test_time = datetime.utcnow()
    with patch('scheduler.scheduler.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = test_time
        await scheduler._handle_job_event(error_event)
    
    # Verify error was recorded
    scheduler.jobs.store.record_scheduler_run.assert_awaited_once_with(
        'test_job',
        'error',
        {'error': str(error_event.exception), 'timestamp': test_time}
    )

@pytest.mark.asyncio
async def test_full_site_scan_job(scheduler_jobs):
    """Test full site scan job execution."""
    # Mock successful crawler run
    mock_stats = {'books_processed': 100, 'errors': 0}
    
    with patch('scheduler.jobs.BooksCrawler') as MockCrawler:
        mock_crawler = AsyncMock()
        mock_crawler.run = AsyncMock(return_value=mock_stats)
        MockCrawler.return_value = mock_crawler
        
        result = await scheduler_jobs.full_site_scan()
        
        assert result == mock_stats
        assert scheduler_jobs.store.record_scheduler_run.await_count == 2  # start and success

@pytest.mark.asyncio
async def test_change_detection_job(scheduler_jobs):
    """Test change detection job execution."""
    # Mock successful change detection
    mock_changes = {'book1': ['price_changed', 'description_updated']}
    mock_report = AsyncMock()
    mock_report.total_books = 50
    mock_report.updated_books = 5
    mock_report.changes_by_type = mock_changes
    
    scheduler_jobs.change_tracker.__aenter__ = AsyncMock(return_value=scheduler_jobs.change_tracker)
    scheduler_jobs.change_tracker.__aexit__ = AsyncMock(return_value=None)
    scheduler_jobs.change_tracker.get_daily_changes = AsyncMock(return_value=mock_report)
    scheduler_jobs.reporter.record_change = AsyncMock()
    scheduler_jobs.reporter.generate_daily_report = AsyncMock()
    
    result = await scheduler_jobs.detect_changes()
    
    assert result.total_books == 50
    assert result.updated_books == 5
    assert scheduler_jobs.store.record_scheduler_run.await_count == 2  # start and success

@pytest.mark.asyncio
async def test_maintenance_job(scheduler_jobs):
    """Test maintenance job execution."""
    result = await scheduler_jobs.maintenance()
    
    assert 'tasks_completed' in result
    assert len(result['tasks_completed']) == 3
    assert scheduler_jobs.store.record_scheduler_run.await_count == 2

@pytest.mark.asyncio
async def test_health_check_job(scheduler_jobs):
    """Test health check job execution."""
    result = await scheduler_jobs.health_check()
    
    assert 'crawler_metrics' in result
    assert 'recent_jobs' in result
    assert 'database_status' in result
    assert result['database_status']['status'] == 'connected'

@pytest.mark.asyncio
async def test_scheduler_graceful_shutdown(scheduler):
    """Test scheduler graceful shutdown."""
    # Create mock scheduler
    mock_scheduler = Mock()
    mock_scheduler.running = True
    mock_scheduler.shutdown = Mock()
    mock_scheduler.add_listener = Mock()
    mock_scheduler.add_job = Mock()

    # Replace the scheduler in our instance
    scheduler.scheduler = mock_scheduler

    # Mock database initialization
    with patch('scheduler.scheduler.init_scheduler_db') as mock_init_db:
        mock_init_db.return_value = None
        
        # Start the scheduler
        await scheduler.start()

        # Verify scheduler is running
        assert mock_scheduler.running is True
        
        # Verify start was called
        mock_scheduler.start.assert_called_once()

        # Shutdown
        scheduler.shutdown()

        # Verify shutdown was called
        mock_scheduler.shutdown.assert_called_once_with()
@pytest.mark.asyncio
async def test_scheduler_retry_logic(scheduler_jobs):
    """Test job retry logic for transient failures."""
    # Mock notifications and sleep
    scheduler_jobs.notifications = AsyncMock()
    
    # Mock failures for all attempts
    fail_count = [0]
    max_retries = 3
    
    async def mock_operation():
        fail_count[0] += 1
        # Always fail
        raise Exception(f"Transient error (attempt {fail_count[0]})")
    
    scheduler_jobs.store.record_scheduler_run = AsyncMock()
    with patch('scheduler.jobs.BooksCrawler') as MockCrawler, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        mock_crawler = AsyncMock()
        mock_crawler.run = mock_operation
        MockCrawler.return_value = mock_crawler
        
        # Record start time for verification
        job_start = datetime.utcnow()
        with patch('scheduler.jobs.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = job_start
            
            # Execute with retries - should fail after max attempts
            with pytest.raises(Exception) as exc_info:
                await scheduler_jobs.full_site_scan()
            
            # Verify proper number of attempts and final error
            assert fail_count[0] == max_retries + 1  # Initial try + retries
            assert str(exc_info.value) == f"Transient error (attempt {fail_count[0]})"
            assert mock_sleep.await_count == max_retries  # Sleep called between retries
            
            # Verify error was recorded
            scheduler_jobs.store.record_scheduler_run.assert_awaited_with(
                'full_site_scan',
                'error',
                {
                    'start_time': job_start,
                    'error_time': job_start,
                    'attempts': max_retries + 1,
                    'error': str(exc_info.value)
                }
            )
            
            # Verify notifications were sent
            scheduler_jobs.notifications.notify_error.assert_awaited_with(
                'full_site_scan',
                'execution_error',
                str(exc_info.value),
                critical=True
            )