# scheduler/jobs.py

"""
Scheduler job definitions and implementations.
Integrates with the crawler for data collection and change detection.
"""

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

from crawler.runner import BooksCrawler
from crawler.store import MongoStore
from .change_tracker import BookChangeTracker
from .db_setup import SchedulerStore
from .models import DailyChangeReport
from .reporting import ChangeReporter
from .notifications import NotificationManager

logger = logging.getLogger('scheduler')

class SchedulerJobs:
    """Implements scheduler jobs with error handling and monitoring."""
    
    def __init__(self):
        """Initialize scheduler jobs with store access."""
        self.store = SchedulerStore()
        self.change_tracker = BookChangeTracker()
        self.reporter = ChangeReporter()
        self.notifications = NotificationManager()
    
    async def full_site_scan(self) -> Dict[str, Any]:
        """
        Execute a full site scan using the crawler.
        Includes error handling and retry logic.
        
        Returns:
            Dict[str, Any]: Scan results and statistics
        Raises:
            Exception: If all retry attempts fail
        """
        job_start = datetime.utcnow()
        max_retries = 3
        retry_delay = 1
        attempt = 0
        
        while attempt <= max_retries:  # Allows for initial try + max_retries attempts
            try:
                # Record job start or retry
                await self.store.record_scheduler_run(
                    'full_site_scan',
                    'running',
                    {'start_time': job_start, 'attempt': attempt}
                )
                
                # Initialize crawler
                crawler = BooksCrawler(checkpoint_interval=20)
                
                # Run the crawler
                stats = await crawler.run()
                
                # Record successful completion
                await self.store.record_scheduler_run(
                    'full_site_scan',
                    'success',
                    {
                        'start_time': job_start,
                        'end_time': datetime.utcnow(),
                        'attempts': attempt,
                        'statistics': stats
                    }
                )
                
                logger.info(f"Full site scan completed successfully: {stats}")
                return stats
                
            except Exception as e:
                if attempt >= max_retries:  # No more retries left
                    # Record final failure
                    await self.store.record_scheduler_run(
                        'full_site_scan',
                        'error',
                        {
                            'start_time': job_start,
                            'error_time': datetime.utcnow(),
                            'attempts': attempt + 1,
                            'error': str(e)
                        }
                    )
                    
                    # Send error notification
                    await self.notifications.notify_error(
                        'full_site_scan',
                        'execution_error',
                        str(e),
                        critical=True
                    )
                    
                    logger.error(f"Full site scan failed after {attempt + 1} attempts: {e}", exc_info=True)
                    raise
                
                # Log retry attempt
                logger.warning(f"Full site scan failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                attempt += 1
    
    async def detect_changes(self) -> Optional[DailyChangeReport]:
        """
        Run change detection on recently crawled books.
        
        Returns:
            Optional[DailyChangeReport]: Report of detected changes
        """
        job_start = datetime.utcnow()
        
        try:
            # Record job start
            await self.store.record_scheduler_run(
                'change_detection',
                'running',
                {'start_time': job_start}
            )
            
            # Get last successful run time
            last_run = await self.store.get_last_successful_run('change_detection')
            
            # Get changes since last run
            async with self.change_tracker as tracker:
                report = await tracker.get_daily_changes(
                    last_run or (job_start - timedelta(days=1))
                )
                
                # Record detected changes in reporting system
                for book_id, changes in report.changes_by_type.items():
                    await self.reporter.record_change(str(book_id), changes)
                
                # Generate daily report
                daily_report = await self.reporter.generate_daily_report(job_start)
            
            # Record successful completion
            await self.store.record_scheduler_run(
                'change_detection',
                'success',
                {
                    'start_time': job_start,
                    'end_time': datetime.utcnow(),
                    'changes_detected': report.total_books
                }
            )
            
            logger.info(
                f"Change detection completed: {report.total_books} books processed, "
                f"{report.updated_books} changes detected"
            )
            return report
            
        except Exception as e:
            error_details = {
                'start_time': job_start,
                'error_time': datetime.utcnow(),
                'error': str(e)
            }
            await self.store.record_scheduler_run(
                'change_detection',
                'error',
                error_details
            )
            logger.error(f"Change detection failed: {e}", exc_info=True)
            raise
    
    async def maintenance(self) -> Dict[str, Any]:
        """
        Run maintenance tasks like cleanup and optimization.
        
        Returns:
            Dict[str, Any]: Maintenance results and statistics
        """
        job_start = datetime.utcnow()
        
        try:
            # Record job start
            await self.store.record_scheduler_run(
                'maintenance',
                'running',
                {'start_time': job_start}
            )
            
            stats = {
                'start_time': job_start,
                'tasks_completed': []
            }
            
            # Consolidate old changes
            async with self.change_tracker as tracker:
                await tracker.consolidate_old_changes(days_threshold=30)
                stats['tasks_completed'].append('change_consolidation')
            
            # Clean up old HTML snapshots
            cleanup_date = datetime.utcnow() - timedelta(days=60)
            await self.store.cleanup_old_snapshots(cleanup_date)
            stats['tasks_completed'].append('snapshot_cleanup')
            
            # Remove orphaned records
            removed = await self.store.remove_orphaned_snapshots()
            stats['orphaned_snapshots_removed'] = removed
            stats['tasks_completed'].append('orphan_cleanup')
            
            # Record successful completion
            await self.store.record_scheduler_run(
                'maintenance',
                'success',
                {
                    'start_time': job_start,
                    'end_time': datetime.utcnow(),
                    'statistics': stats
                }
            )
            
            logger.info(f"Maintenance completed successfully: {stats}")
            return stats
            
        except Exception as e:
            error_details = {
                'start_time': job_start,
                'error_time': datetime.utcnow(),
                'error': str(e)
            }
            await self.store.record_scheduler_run(
                'maintenance',
                'error',
                error_details
            )
            logger.error(f"Maintenance job failed: {e}", exc_info=True)
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the crawler and scheduler systems.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            # Get crawler metrics
            crawler_metrics = await self.store.get_crawl_metrics()
            
            # Get recent job stats
            recent_jobs = await self.get_recent_job_stats()
            
            # Check database health
            db_status = await self.check_database_health()
            
            health_status = {
                'timestamp': datetime.utcnow(),
                'crawler_metrics': crawler_metrics,
                'recent_jobs': recent_jobs,
                'database_status': db_status,
                'overall_status': 'healthy'
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {
                'timestamp': datetime.utcnow(),
                'status': 'error',
                'error': str(e)
            }
    
    async def get_recent_job_stats(self) -> Dict[str, Any]:
        """Get statistics about recent job runs."""
        cutoff = datetime.utcnow() - timedelta(days=1)
        
        pipeline = [
            {
                '$match': {
                    'timestamp': {'$gte': cutoff},
                    'scheduler_type': {
                        '$in': ['full_site_scan', 'change_detection', 'maintenance']
                    }
                }
            },
            {
                '$group': {
                    '_id': '$scheduler_type',
                    'total_runs': {'$sum': 1},
                    'successful_runs': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'success']}, 1, 0]}
                    },
                    'last_run': {'$max': '$timestamp'},
                    'last_status': {'$last': '$status'}
                }
            }
        ]
        
        job_stats = await self.store.checkpoints.aggregate(pipeline).to_list(None)
        return {stat['_id']: stat for stat in job_stats}
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connection and collection health."""
        try:
            # Test database connection
            await self.store.books.find_one()
            
            # Get collection stats
            stats = {
                'books': await self.store.books.count_documents({}),
                'changes': await self.store.changes.count_documents({}),
                'checkpoints': await self.store.checkpoints.count_documents({})
            }
            
            return {
                'status': 'connected',
                'collection_stats': stats
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }