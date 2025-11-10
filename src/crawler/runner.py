"""Main crawler execution module."""
import asyncio
from typing import Set, List, Optional, Dict, Any
import hashlib
import os
from datetime import datetime
from urllib.parse import urljoin

from .client import CrawlerClient
from .store import MongoStore
from .parsers import (
    extract_categories,
    extract_books_from_list,
    extract_book_data,
    get_next_page_url
)
from .models import Book
from .settings import Settings
import logging

logger = logging.getLogger("books_crawler")
settings = Settings()

class BooksCrawler:
    def __init__(
        self,
        start_url: str = "https://books.toscrape.com/",
        checkpoint_interval: int = 10
    ):
        """Initialize crawler with configuration.
        
        Args:
            start_url: Base URL to start crawling from
            checkpoint_interval: Save checkpoint every N successful crawls
        """
        self.start_url = start_url
        self.checkpoint_interval = checkpoint_interval
        self.store = MongoStore()
        
        # State tracking
        self.seen_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.current_category: Optional[str] = None
        self.books_processed = 0
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def crawl_book_page(self, url: str, category: str) -> Optional[str]:
        """Crawl a single book page.
        
        Args:
            url: URL of the book detail page
            category: Category the book belongs to
            
        Returns:
            str: Book ID if successful, None otherwise
        """
        if url in self.seen_urls:
            return None

        self.seen_urls.add(url)
        async with self.semaphore:
            start_time = asyncio.get_event_loop().time()
            try:
                async with CrawlerClient() as client:
                    status_code, html, final_url = await client.fetch(url)
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if status_code != 200:
                        logger.error(f"Failed to fetch book page {url}: {status_code}")
                        self.failed_urls.add(url)
                        return None
                    
                    # Generate fingerprint for deduplication
                    html_hash = hashlib.sha256(html.encode()).hexdigest()
                    
                    # Extract and validate book data
                    book_data = extract_book_data(html, final_url)
                    book_data.update({
                        'category': category,
                        'raw_html_hash': html_hash,
                        'crawl_timestamp': datetime.utcnow(),
                        'status': 'success',
                        'response_time': response_time,
                        'http_status': status_code
                    })
                    
                    # Create book model and save
                    book = Book(**book_data)
                    book_id = await self.store.upsert_book(book, html)
                    
                    # Update progress
                    self.books_processed += 1
                    
                    # Checkpoint periodically
                    if self.books_processed % self.checkpoint_interval == 0:
                        await self.store.set_checkpoint(url)
                        logger.info(f"Checkpoint saved at {url}")
                    
                    logger.info(f"Successfully crawled book: {book.title}")
                    return book_id
                    
            except Exception as e:
                logger.exception(f"Error crawling {url}: {str(e)}")
                self.failed_urls.add(url)
                return None

    async def crawl_category_page(self, url: str, category: str) -> List[str]:
        """Crawl a category/list page and extract book URLs.
        
        Args:
            url: URL of the category/list page
            category: Name of the category being processed
            
        Returns:
            List[str]: List of processed book IDs
        """
        try:
            async with CrawlerClient() as client:
                status_code, html, final_url = await client.fetch(url)
                if status_code != 200:
                    logger.error(f"Failed to fetch category page {url}: {status_code}")
                    return []
                
                # Extract book URLs from the page
                books = extract_books_from_list(html)
                
                # Process each book concurrently
                tasks = []
                for _, book_url in books:
                    if book_url not in self.seen_urls:
                        task = asyncio.create_task(
                            self.crawl_book_page(book_url, category)
                        )
                        tasks.append(task)
                
                # Wait for all book processing to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                book_ids = [r for r in results if isinstance(r, str)]
                
                # Check for next page
                next_url = get_next_page_url(html, url)
                if next_url:
                    # Process next page recursively
                    next_ids = await self.crawl_category_page(next_url, category)
                    book_ids.extend(next_ids)
                
                return book_ids
                
        except Exception as e:
            logger.exception(f"Error processing category page {url}: {str(e)}")
            return []

    async def run(self, resume_url: Optional[str] = None) -> Dict[str, Any]:
        """Run the crawler.
        
        Args:
            resume_url: Optional URL to resume crawling from
            
        Returns:
            Dict containing crawl statistics
        """
        logger.info("Starting crawler run")
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Initialize or resume
            if resume_url:
                logger.info(f"Resuming crawl from {resume_url}")
                self.seen_urls = set(
                    await self.store.get_processed_urls()
                )
            
            # Get category list
            # Get categories from index page
            async with CrawlerClient() as client:
                status_code, html, _ = await client.fetch(self.start_url)
                if status_code != 200:
                    raise RuntimeError(f"Failed to fetch index page: {status_code}")
                
                categories = extract_categories(html)
            
            logger.info(f"Found {len(categories)} categories from index pages")
            
            # Process each category
            all_book_ids = []
            for category_name, category_url in categories:
                if resume_url and category_url != resume_url:
                    continue
                    
                logger.info(f"Processing category: {category_name}")
                self.current_category = category_name
                
                book_ids = await self.crawl_category_page(category_url, category_name)
                all_book_ids.extend(book_ids)
                
                logger.info(
                    f"Completed category {category_name}: "
                    f"{len(book_ids)} books processed"
                )
                
                resume_url = None  # Reset resume point after finding it
                self.current_category = None
            
            # Compile statistics
            end_time = asyncio.get_event_loop().time()
            stats = {
                'total_books': len(all_book_ids),
                'failed_urls': len(self.failed_urls),
                'categories_processed': len(categories),
                'duration_seconds': end_time - start_time,
                'successful': len(self.failed_urls) == 0
            }
            
            logger.info(f"Crawl completed: {stats}")
            return stats
            
        except Exception as e:
            logger.exception("Crawler run failed")
            raise

async def run_crawler(
    resume_url: Optional[str] = None,
    checkpoint_interval: int = 10
) -> Dict[str, Any]:
    """Convenience function to run the crawler.
    
    Args:
        resume_url: Optional URL to resume crawling from
        checkpoint_interval: Save checkpoint every N successful crawls
        
    Returns:
        Dict containing crawl statistics
    """
    crawler = BooksCrawler(checkpoint_interval=checkpoint_interval)
    return await crawler.run(resume_url)