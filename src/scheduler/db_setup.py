# scheduler/db_setup.py

"""
Database schema management for the scheduler component.
Extends the crawler's existing schema with additional indexes and fields needed for scheduling.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from datetime import datetime

from src.crawler.store import MongoStore
from src.crawler.settings import Settings

logger = logging.getLogger('scheduler')

class SchedulerStore(MongoStore):
    """Extends the crawler's MongoStore with scheduler-specific functionality."""

    async def init_scheduler_indexes(self):
        """
        Initialize additional indexes needed for the scheduler component.
        Extends the crawler's existing indexes without duplicating them.
        """
        try:
            # Create compound index for change tracking with TTL
            await self.changes.create_indexes([
                {
                    'key': [
                        ('timestamp', -1),
                        ('change_type', 1)
                    ],
                    'name': 'scheduler_changes_lookup'
                },
                {
                    'key': [('timestamp', 1)],
                    'name': 'changes_ttl',
                    'expireAfterSeconds': 30 * 24 * 60 * 60  # 30 days
                }
            ])

            # Add index for consolidated changes
            await self.changes.create_index(
                [
                    ('change_type', 1),
                    ('book_id', 1),
                    ('timestamp', -1)
                ],
                name='consolidated_changes_lookup'
            )

            # Create index for scheduler state
            await self.checkpoints.create_index(
                [
                    ('scheduler_type', 1),
                    ('timestamp', -1)
                ],
                name='scheduler_checkpoint_lookup'
            )

            logger.info("Scheduler indexes initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing scheduler indexes: {e}")
            raise

    async def update_schema_version(self):
        """
        Update schema version and add any new fields needed for scheduling.
        """
        try:
            # Update schema version in database
            await self.db.schema_version.update_one(
                {'component': 'scheduler'},
                {
                    '$set': {
                        'version': '1.0.0',
                        'last_updated': datetime.utcnow(),
                        'features': [
                            'change_tracking',
                            'consolidated_changes',
                            'ttl_indexes'
                        ]
                    }
                },
                upsert=True
            )
            logger.info("Schema version updated successfully")
        except Exception as e:
            logger.error(f"Error updating schema version: {e}")
            raise

    async def get_last_successful_run(self, job_type: str) -> Optional[datetime]:
        """
        Get the timestamp of the last successful scheduler run.

        Args:
            job_type: Type of scheduler job ('daily_scan', 'change_detection', etc.)

        Returns:
            Optional[datetime]: Timestamp of last successful run, if any
        """
        checkpoint = await self.checkpoints.find_one(
            {
                'scheduler_type': job_type,
                'status': 'success'
            },
            sort=[('timestamp', -1)]
        )
        return checkpoint['timestamp'] if checkpoint else None

    async def record_scheduler_run(
        self,
        job_type: str,
        status: str,
        details: Optional[dict] = None
    ):
        """
        Record the execution of a scheduler job.

        Args:
            job_type: Type of scheduler job
            status: Execution status ('success', 'error', etc.)
            details: Optional execution details
        """
        await self.checkpoints.insert_one({
            'scheduler_type': job_type,
            'status': status,
            'timestamp': datetime.utcnow(),
            'details': details or {}
        })

async def init_scheduler_db():
    """
    Initialize the scheduler database components.
    Ensures all required collections and indexes exist.
    """
    settings = Settings()
    store = SchedulerStore()
    
    try:
        # First, ensure crawler's basic setup is done
        await store.init_indexes()
        
        # Then add scheduler-specific indexes
        await store.init_scheduler_indexes()
        
        # Update schema version
        await store.update_schema_version()
        
        logger.info("Scheduler database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler database: {e}")
        raise
    finally:
        store.client.close()