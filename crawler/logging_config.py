import logging
from logging.handlers import RotatingFileHandler
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def setup_logging():
    """Configure logging for crawler and scheduler."""
    logger = logging.getLogger("books_crawler")
    logger.setLevel(logging.INFO)

    # Console handler (prints to terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # File handler (rotates when file grows too large)
    file_handler = RotatingFileHandler(
        "logs/crawler.log", maxBytes=5_000_000, backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Define consistent log message format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
