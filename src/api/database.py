"""
Database Connection Management

Provides async MongoDB connection with proper lifecycle management.
Implements singleton pattern for connection pooling and reuse.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from src.api.settings import settings
from src.utils.logging import log_database_operation
import logging

logger = logging.getLogger("api.database")


class Database:
    """
    Database connection wrapper implementing singleton pattern.
    
    Attributes:
        client: MongoDB async client instance
        db: MongoDB database instance
    """
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    _connected: bool = False


# Global database instance
db = Database()


async def connect_to_mongo():
    """
    Connect to MongoDB on application startup.
    
    Establishes connection pool and validates connectivity.
    Uses settings from src.api.config for connection string.
    
    Raises:
        ConnectionFailure: If unable to connect to MongoDB
    """
    try:
        logger.info("Connecting to MongoDB...")
        logger.info(f"MongoDB URI: {settings.mongo_uri[:30]}...")
        
        # Create async MongoDB client with connection pooling
        db.client = AsyncIOMotorClient(
            settings.mongo_uri,
            maxPoolSize=50,  # Maximum connections in pool
            minPoolSize=10,  # Minimum connections to maintain
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,  # 10 second connection timeout
            socketTimeoutMS=20000,  # 20 second socket timeout
        )
        
        # Extract database name from URI or use default
        # URI format: mongodb://host:port/database_name
        if '/' in settings.mongo_uri.split('://')[1]:
            db_name = settings.mongo_uri.split('/')[-1].split('?')[0]
        else:
            db_name = "books_db"  # Default database name
        
        db.db = db.client[db_name]
        
        # Test connection by pinging the server
        await db.client.admin.command('ping')
        
        db._connected = True
        logger.info(f"Successfully connected to MongoDB database: {db_name}")
        
        # Log collection info
        collections = await db.db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Check if books collection exists
        if "books" in collections:
            book_count = await db.db.books.count_documents({})
            logger.info(f"Books collection contains {book_count} documents")
            log_database_operation(
                logger,
                operation="startup_check",
                collection="books",
                count=book_count,
                status="success"
            )
        else:
            logger.warning("Books collection not found - may need to run crawler first")
            
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        db._connected = False
        raise ConnectionFailure(
            f"Could not connect to MongoDB at {settings.mongo_uri[:30]}... - {e}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        db._connected = False
        raise


async def close_mongo_connection():
    """
    Close MongoDB connection on application shutdown.
    
    Properly closes all connections in the pool and cleans up resources.
    """
    if db.client is not None:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        db.client = None
        db.db = None
        db._connected = False
        logger.info("✅ MongoDB connection closed")
    else:
        logger.info("MongoDB connection already closed or never established")


def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency for injecting database into endpoints.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Raises:
        RuntimeError: If database is not connected
        
    Example:
        @app.get("/books")
        async def list_books(db: AsyncIOMotorDatabase = Depends(get_database)):
            books = await db.books.find().to_list(length=10)
            return books
    """
    if db.db is None or not db._connected:
        raise RuntimeError(
            "Database not connected. Ensure connect_to_mongo() was called on startup."
        )
    return db.db


async def check_database_health() -> dict:
    """
    Check database health and connectivity.
    
    Returns:
        dict: Health status with connection info and statistics
        
    Example response:
        {
            "status": "connected",
            "database": "books_db",
            "collections": 2,
            "books_count": 1000
        }
    """
    if not db._connected or db.client is None:
        return {
            "status": "disconnected",
            "database": None,
            "error": "Database connection not established"
        }
    
    try:
        # Ping database to check connectivity
        await db.client.admin.command('ping')
        
        # Get database info
        db_name = db.db.name
        collections = await db.db.list_collection_names()
        
        # Get books count if collection exists
        books_count = 0
        if "books" in collections:
            books_count = await db.db.books.count_documents({})
        
        return {
            "status": "connected",
            "database": db_name,
            "collections": len(collections),
            "books_count": books_count,
            "ping": "ok"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "database": db.db.name if db.db else None,
            "error": str(e)
        }
