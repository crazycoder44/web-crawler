"""
Pytest configuration and fixtures for integration tests.

Provides test client, database connection, and test data fixtures.
"""

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator

from src.api.main import app
from src.api.settings import settings
from src.api.auth.api_key import hash_api_key


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    return settings


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Get test database connection."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    # Extract database name from mongo_uri (format: mongodb://host:port/dbname)
    db_name = settings.mongo_uri.split("/")[-1] if "/" in settings.mongo_uri else "books"
    db = client[db_name]
    yield db
    client.close()


@pytest.fixture(scope="session")
def valid_api_key():
    """
    Get a valid PLAIN API key for testing.
    
    Returns the plain key that clients use in X-API-Key header.
    The corresponding hash is stored in .env: 
    2688f4e126ca5efd4a60022073e6cd90017626e56c3f30b194d53e6299edfe3c
    """
    return "test-api-key-12345"


@pytest.fixture(scope="session")
def invalid_api_key():
    """Get an invalid API key for testing."""
    return "invalid-key-xyz-999"


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for the API.
    
    This client can make requests to all endpoints without running a server.
    Manually triggers startup to ensure database connection.
    """
    from src.utils.database import connect_to_mongo, close_mongo_connection
    
    # Manually trigger startup to connect database
    await connect_to_mongo()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Cleanup: disconnect database
    await close_mongo_connection()


@pytest_asyncio.fixture(scope="session")
async def sample_book_id(test_db) -> str:
    """Get a valid book ID from the database."""
    book = await test_db.books.find_one()
    if book:
        return str(book["_id"])
    return "507f1f77bcf86cd799439011"  # Fallback


@pytest_asyncio.fixture(scope="session")
async def sample_book_category(test_db) -> str:
    """Get a valid category from the database."""
    book = await test_db.books.find_one({"category": {"$exists": True, "$ne": None}})
    if book and book.get("category"):
        return book["category"]
    return "Fiction"  # Fallback


@pytest_asyncio.fixture(scope="session")
async def total_books_count(test_db) -> int:
    """Get total count of books in database."""
    count = await test_db.books.count_documents({})
    return count


@pytest_asyncio.fixture(scope="session")
async def total_changes_count(test_db) -> int:
    """Get total count of changes in database."""
    count = await test_db.book_changes.count_documents({})
    return count
