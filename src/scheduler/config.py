# scheduler/config.py

"""
Configuration for the APScheduler instance.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Create scheduler instance
scheduler = AsyncIOScheduler()

# Configure default settings
DEFAULT_SCHEDULER_CONFIG = {
    'apscheduler.timezone': 'UTC',
    'apscheduler.jobstores.default': {
        'type': 'mongodb'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.asyncio:AsyncIOExecutor',
        'max_workers': 10
    }
}

# Job configurations
JOBS = {
    'daily_scan': {
        'trigger': CronTrigger(hour=0, minute=0),  # Run at midnight
        'max_instances': 1,
        'coalesce': True,
        'misfire_grace_time': 3600  # 1 hour grace time
    },
    'change_detection': {
        'trigger': CronTrigger(hour='*/4'),  # Run every 4 hours
        'max_instances': 1,
        'coalesce': True,
        'misfire_grace_time': 1800  # 30 minutes grace time
    }
}