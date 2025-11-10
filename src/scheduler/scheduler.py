# scheduler/scheduler.py

"""
Main scheduler configuration and setup.
Configures APScheduler with jobs and error handling.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import asyncio

from .jobs import SchedulerJobs
from .db_setup import init_scheduler_db

logger = logging.getLogger('scheduler')

class BookScheduler:
    """Main scheduler class managing all book crawling and monitoring jobs."""
    
    def __init__(self):
        """Initialize the scheduler with jobs and error handling."""
        self.scheduler = AsyncIOScheduler()
        self.jobs = SchedulerJobs()
        
        # Configure error handling
        self.scheduler.add_listener(
            self._handle_job_event,
            EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )
        
        # Configure jobs
        self._configure_jobs()
    
    def _configure_jobs(self):
        """Configure all scheduler jobs with appropriate triggers."""
        # Full site scan - daily at 2 AM
        self.scheduler.add_job(
            self.jobs.full_site_scan,
            CronTrigger(hour=2, minute=0),
            id='full_site_scan',
            name='Daily Full Site Scan',
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600  # 1 hour
        )
        
        # Change detection - every 4 hours
        self.scheduler.add_job(
            self.jobs.detect_changes,
            CronTrigger(hour='*/4'),
            id='change_detection',
            name='Change Detection',
            coalesce=True,
            max_instances=1,
            misfire_grace_time=1800  # 30 minutes
        )
        
        # Maintenance - daily at 3 AM
        self.scheduler.add_job(
            self.jobs.maintenance,
            CronTrigger(hour=3, minute=0),
            id='maintenance',
            name='Daily Maintenance',
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600  # 1 hour
        )
        
        # Health check - every 15 minutes
        self.scheduler.add_job(
            self.jobs.health_check,
            CronTrigger(minute='*/15'),
            id='health_check',
            name='Health Check',
            coalesce=True,
            max_instances=1,
            misfire_grace_time=300  # 5 minutes
        )
    
    async def _handle_job_event(self, event):
        """Handle job execution events and errors."""
        if event.exception:
            logger.error(
                f"Job {event.job_id} failed: {str(event.exception)}",
                exc_info=event.exception
            )
            
            # Record error in database
            try:
                await self.jobs.store.record_scheduler_run(
                    event.job_id,
                    'error',
                    {
                        'error': str(event.exception),
                        'timestamp': datetime.utcnow()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to record job error: {e}")
        else:
            logger.info(f"Job {event.job_id} completed successfully")
    
    async def start(self):
        """Start the scheduler after initializing the database."""
        try:
            # Initialize database
            await init_scheduler_db()
            
            # Start the scheduler
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
            raise

async def run_scheduler():
    """Run the scheduler as an async context manager."""
    scheduler = BookScheduler()
    try:
        await scheduler.start()
        # Keep the scheduler running
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        scheduler.shutdown()
        raise