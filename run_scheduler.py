#!/usr/bin/env python3
"""
Entry point for running the scheduler service.
Manages scheduled crawling and change detection.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scheduler.scheduler import run_scheduler
import src.scheduler.logging_config  # Import to initialize loggers

def main():
    """Configure logging and start the scheduler."""
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