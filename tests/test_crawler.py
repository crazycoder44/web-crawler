"""Test script for the books crawler."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from src.crawler.runner import run_crawler
from src.crawler.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("crawler_test")
settings = Settings()

async def verify_mongodb_connection() -> bool:
    """Verify MongoDB connection is working."""
    try:
        client = AsyncIOMotorClient(settings.mongo_uri)
        await client.admin.command('ping')
        logger.info("MongoDB connection successful")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False

async def get_crawl_results() -> Dict[str, Any]:
    """Get statistics about crawled data."""
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client.get_default_database()
    
    stats = {
        'total_books': await db.books.count_documents({}),
        'categories': await db.books.distinct('category'),
        'error_count': await db.books.count_documents({'status': 'error'}),
        'books_with_description': await db.books.count_documents({
            'description': {'$exists': True, '$ne': None}
        }),
        'price_range': await db.books.aggregate([
            {
                '$group': {
                    '_id': None,
                    'min_price': {'$min': '$price_incl_tax'},
                    'max_price': {'$max': '$price_incl_tax'},
                    'avg_price': {'$avg': '$price_incl_tax'}
                }
            }
        ]).to_list(1),
        'ratings_distribution': await db.books.aggregate([
            {
                '$group': {
                    '_id': '$rating',
                    'count': {'$sum': 1}
                }
            }
        ]).to_list(None)
    }
    
    # Get sample successful and failed books
    stats['sample_success'] = await db.books.find_one({'status': 'success'})
    stats['sample_error'] = await db.books.find_one({'status': 'error'})
    
    return stats

async def main():
    """Run crawler test and verify results."""
    logger.info("Starting crawler test")
    
    # Verify MongoDB connection
    if not await verify_mongodb_connection():
        logger.error("MongoDB connection failed, aborting test")
        return
    
    try:
        # Run the crawler
        start_time = datetime.now()
        crawl_stats = await run_crawler()
        duration = datetime.now() - start_time
        
        logger.info(f"Crawl completed in {duration}")
        logger.info(f"Crawl statistics: {crawl_stats}")
        
        # Verify results
        results = await get_crawl_results()
        
        # Log detailed results
        logger.info("\n=== Crawl Results ===")
        logger.info(f"Total books crawled: {results['total_books']}")
        logger.info(f"Categories found: {len(results['categories'])}")
        logger.info(f"Error count: {results['error_count']}")
        logger.info(f"Books with descriptions: {results['books_with_description']}")
        
        if results['price_range']:
            price_stats = results['price_range'][0]
            logger.info(
                f"Price range: £{price_stats['min_price']:.2f} - "
                f"£{price_stats['max_price']:.2f} "
                f"(avg: £{price_stats['avg_price']:.2f})"
            )
        
        logger.info("\nRating distribution:")
        for rating in results['ratings_distribution']:
            logger.info(f"{rating['_id']} stars: {rating['count']} books")
        
        # Verify completeness
        expected_books = 1000  # books.toscrape.com has 1000 books
        if results['total_books'] >= expected_books:
            logger.info("✓ Successfully crawled all books")
        else:
            logger.warning(
                f"⚠ Only crawled {results['total_books']} out of "
                f"{expected_books} expected books"
            )
        
        # Sample book validation
        if results['sample_success']:
            book = results['sample_success']
            logger.info("\nSample successful book:")
            logger.info(f"Title: {book.get('title')}")
            logger.info(f"Category: {book.get('category')}")
            logger.info(f"Price: £{book.get('price_incl_tax')}")
            logger.info(f"Rating: {book.get('rating')} stars")
        
    except Exception as e:
        logger.exception("Test failed with error")
    
if __name__ == "__main__":
    asyncio.run(main())