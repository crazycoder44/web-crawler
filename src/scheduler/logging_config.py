# scheduler/logging_config.py

"""
Logging configuration for the scheduler module.
"""

import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory at project root (go up 3 levels: scheduler -> src -> root)
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure scheduler logger
scheduler_logger = logging.getLogger('scheduler')
scheduler_logger.setLevel(logging.INFO)

# File handler for scheduler logs
scheduler_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'scheduler.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
scheduler_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
scheduler_handler.setFormatter(formatter)

# Add handler to logger
scheduler_logger.addHandler(scheduler_handler)

# Configure change detection logger
change_logger = logging.getLogger('change_detection')
change_logger.setLevel(logging.INFO)

# File handler for change detection logs
change_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'changes.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
change_handler.setLevel(logging.INFO)
change_handler.setFormatter(formatter)
change_logger.addHandler(change_handler)