"""Quick test to verify MongoDB connection and settings for both crawler and scheduler."""
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from crawler.settings import Settings as CrawlerSettings
from scheduler.settings import Settings as SchedulerSettings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_crawler_connection():
    """Test MongoDB connection for crawler."""
    settings = CrawlerSettings()
    logger.info(f"Loaded crawler settings: {settings.model_dump()}")
    
    try:
        client = AsyncIOMotorClient(settings.mongo_uri)
        # Test the connection
        await client.admin.command('ping')
        logger.info("✓ Crawler: Successfully connected to MongoDB")
        
        # Test database access
        db = client.get_default_database()
        # Try to create a test collection
        await db.create_collection('test_crawler_collection')
        logger.info("✓ Crawler: Successfully created test collection")
        
        # Clean up
        await db.drop_collection('test_crawler_collection')
        logger.info("✓ Crawler: Successfully cleaned up test collection")
        
        client.close()
        assert True, "Crawler MongoDB connection test successful"
        
    except Exception as e:
        logger.error(f"Crawler connection test failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_scheduler_connection():
    """Test MongoDB connection for scheduler."""
    settings = SchedulerSettings()
    logger.info(f"Loaded scheduler settings - MongoDB URL: {settings.mongodb_url}")
    
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        # Test the connection
        await client.admin.command('ping')
        logger.info("✓ Scheduler: Successfully connected to MongoDB")
        
        # Test database access (scheduler uses 'books' database)
        db = client['books']
        # Try to create a test collection
        await db.create_collection('test_scheduler_collection')
        logger.info("✓ Scheduler: Successfully created test collection")
        
        # Clean up
        await db.drop_collection('test_scheduler_collection')
        logger.info("✓ Scheduler: Successfully cleaned up test collection")
        
        client.close()
        assert True, "Scheduler MongoDB connection test successful"
        
    except Exception as e:
        logger.error(f"Scheduler connection test failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_both_connections():
    """Test that both crawler and scheduler can connect simultaneously."""
    crawler_settings = CrawlerSettings()
    scheduler_settings = SchedulerSettings()
    
    try:
        # Connect both
        crawler_client = AsyncIOMotorClient(crawler_settings.mongo_uri)
        scheduler_client = AsyncIOMotorClient(scheduler_settings.mongodb_url)
        
        # Test both connections
        await crawler_client.admin.command('ping')
        await scheduler_client.admin.command('ping')
        
        logger.info("✓ Both crawler and scheduler successfully connected to MongoDB")
        
        # Clean up
        crawler_client.close()
        scheduler_client.close()
        
        assert True, "Both connections successful"
        
    except Exception as e:
        logger.error(f"Simultaneous connection test failed: {str(e)}")
        raise