"""Quick test to verify MongoDB connection and settings."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from crawler.settings import Settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    settings = Settings()
    logger.info(f"Loaded settings: {settings.dict()}")
    
    try:
        client = AsyncIOMotorClient(settings.mongo_uri)
        # Test the connection
        await client.admin.command('ping')
        logger.info("✓ Successfully connected to MongoDB")
        
        # Test database access
        db = client.get_default_database()
        # Try to create a test collection
        await db.create_collection('test_collection')
        logger.info("✓ Successfully created test collection")
        
        # Clean up
        await db.drop_collection('test_collection')
        logger.info("✓ Successfully cleaned up test collection")
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection())