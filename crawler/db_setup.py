"""MongoDB schema and index setup."""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging

logger = logging.getLogger("books_crawler")

async def init_mongodb(
    connection_string: str,
    db_name: str = "books_crawler"
) -> None:
    """Initialize MongoDB collections and indexes.
    
    Args:
        connection_string: MongoDB connection URI
        db_name: Name of the database to use
    """
    client = AsyncIOMotorClient(connection_string)
    db = client[db_name]
    
    # Create books collection indexes
    await db.books.create_indexes([
        # Unique index on source_url to prevent duplicates
        {
            'key': [('source_url', 1)],
            'unique': True,
            'name': 'unique_source_url'
        },
        # Index for category searches
        {
            'key': [('category', 1)],
            'name': 'category_lookup'
        },
        # Index for price range queries
        {
            'key': [('price_incl_tax', 1)],
            'name': 'price_lookup'
        },
        # Index for rating searches
        {
            'key': [('rating', 1)],
            'name': 'rating_lookup'
        },
        # Index for crawl timestamp (useful for finding recent changes)
        {
            'key': [('crawl_timestamp', -1)],
            'name': 'crawl_time_lookup'
        }
    ])
    
    # Create book_changes collection indexes
    await db.book_changes.create_indexes([
        # Index for finding changes by book
        {
            'key': [('book_id', 1), ('timestamp', -1)],
            'name': 'book_changes_lookup'
        }
    ])
    
    # Create checkpoints collection index
    await db.checkpoints.create_index(
        [('checkpoint_type', 1)],
        unique=True,
        name='unique_checkpoint_type'
    )
    
    logger.info("MongoDB collections and indexes initialized successfully")

# Document schemas (for reference)
BOOKS_SCHEMA = {
    'title': str,               # Book title
    'description': str,         # Book description
    'category': str,           # Book category
    'price_incl_tax': float,   # Price including tax
    'price_excl_tax': float,   # Price excluding tax
    'availability': str,       # Availability status
    'num_reviews': int,        # Number of reviews
    'rating': int,            # Rating (1-5)
    'image_url': str,         # URL to book image
    'source_url': str,        # URL where book was found
    'crawl_timestamp': str,   # ISO timestamp of last crawl
    'status': str,           # Crawl status (success/error)
    'raw_html_hash': str,    # Hash of raw HTML content
    'raw_html_snapshot_path': str,  # Path to stored HTML snapshot
    'response_time': float,  # Time taken to fetch page
    'http_status': int      # HTTP status code
}

BOOK_CHANGES_SCHEMA = {
    'book_id': str,          # Reference to books collection
    'timestamp': str,        # ISO timestamp of change
    'changes': dict,         # Fields that changed with old/new values
    'change_type': str      # Type of change (update/delete)
}

CHECKPOINTS_SCHEMA = {
    'checkpoint_type': str,  # Type of checkpoint (page/category)
    'value': str,           # Checkpoint value (URL or page number)
    'timestamp': str        # ISO timestamp of checkpoint
}