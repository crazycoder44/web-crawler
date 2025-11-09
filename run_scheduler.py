"""
Main entry point for running the scheduler service.
"""

import asyncio
import logging.config
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from scheduler.scheduler import run_scheduler
from scheduler.logging_config import LOGGING_CONFIG

def main():
    """Configure logging and start the scheduler."""
    # Configure logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger('scheduler')
    
    logger.info("Starting scheduler service...")
    
    try:
        # Run the scheduler
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Scheduler service stopped by user")
    except Exception as e:
        logger.error(f"Scheduler service failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()