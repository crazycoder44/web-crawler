"""MongoDB storage layer for book data with change tracking and GridFS support."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import hashlib
from bson import ObjectId
from .models import Book
from .settings import Settings
import logging

logger = logging.getLogger("books_crawler")
settings = Settings()

class MongoStore:
    def __init__(self):
        """Initialize MongoDB connections and collections."""
        self.client = AsyncIOMotorClient(settings.mongo_uri)
        self.db = self.client.get_default_database()
        self.books = self.db.books
        self.changes = self.db.book_changes
        self.checkpoints = self.db.checkpoints
        self.fs = AsyncIOMotorGridFSBucket(self.db) if settings.store_html_in_gridfs else None

    async def init_indexes(self):
        """Create required indexes for all collections."""
        # Books collection indexes
        from pymongo import IndexModel
        # Create IndexModel instances for each index
        await self.books.create_indexes([
            IndexModel([('source_url', 1)], unique=True, name='unique_source_url'),
            IndexModel([('category', 1)], name='category_lookup'),
            IndexModel([('price_incl_tax', 1)], name='price_lookup'),
            IndexModel([('rating', 1)], name='rating_lookup'),
            IndexModel([('crawl_timestamp', -1)], name='crawl_time_lookup')
        ])
        
        # Book changes collection index
        await self.changes.create_indexes([
            IndexModel([('book_id', 1), ('timestamp', -1)], name='book_changes_lookup')
        ])
        
        # Checkpoints collection index
        await self.checkpoints.create_index(
            [('checkpoint_type', 1)],
            unique=True,
            name='unique_checkpoint_type'
        )
        
        logger.info("MongoDB indexes initialized successfully")

    async def compute_html_hash(self, html: str) -> str:
        """Compute SHA-256 hash of HTML content."""
        return hashlib.sha256(html.encode('utf-8')).hexdigest()

    async def store_html_snapshot(self, book_id: str, html: str) -> str:
        """Store HTML snapshot in GridFS or filesystem."""
        html_hash = await self.compute_html_hash(html)
        
        if settings.store_html_in_gridfs:
            filename = f"{book_id}_{html_hash}.html"
            grid_out = await self.fs.upload_from_stream(
                filename,
                html.encode('utf-8'),
                metadata={'book_id': book_id, 'hash': html_hash}
            )
            return str(grid_out)
        else:
            # Handle filesystem storage here if needed
            return html_hash

    async def upsert_book(self, book: Book, html: str) -> str:
        """Insert or update a book document and track changes.
        
        Args:
            book: Book model instance
            html: Raw HTML content of the book page
            
        Returns:
            str: The book's ObjectId as string
        """
        # Compute HTML hash
        html_hash = await self.compute_html_hash(html)
        book_id = book.id if book.id else None
        html_snapshot_id = await self.store_html_snapshot(book_id, html)
        
        # Prepare book document and convert HttpUrl fields to strings
        book_dict = book.model_dump()
        if 'source_url' in book_dict:
            book_dict['source_url'] = str(book_dict['source_url'])
        if 'image_url' in book_dict:
            book_dict['image_url'] = str(book_dict['image_url']) if book_dict['image_url'] else None
            
        book_dict.update({
            'raw_html_hash': html_hash,
            'raw_html_snapshot_path': html_snapshot_id,
            'crawl_timestamp': datetime.utcnow(),
        })
        
        # Check for existing document
        existing = await self.get_book_by_url(book.source_url)
        
        if existing:
            # Detect changes
            changes = {
                k: {'old': existing.get(k), 'new': v}
                for k, v in book_dict.items()
                if k in existing and existing.get(k) != v
            }
            
            if changes:
                # Update book
                result = await self.books.find_one_and_update(
                    {'_id': existing['_id']},
                    {'$set': book_dict},
                    return_document=True
                )
                
                # Update book model with ID
                book.id = str(existing['_id'])
                
                # Record changes
                await self.record_change(str(existing['_id']), changes)
                logger.info(f"Updated book {book.title} with {len(changes)} changes")
            else:
                result = existing
                # Update book model with ID
                book.id = str(existing['_id'])
                logger.debug(f"No changes detected for book {book.title}")
        else:
            # Insert new book
            result = await self.books.insert_one(book_dict)
            # Update book model with new ID
            book.id = str(result.inserted_id)
            logger.info(f"Inserted new book {book.title}")
            
        return str(result['_id'] if isinstance(result, dict) else result.inserted_id)

    async def get_book_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve a book by its source URL."""
        url_str = str(url)  # Convert HttpUrl to string
        return await self.books.find_one({'source_url': url_str})

    async def record_change(self, book_id: str, changes: Dict[str, Any]):
        """Record changes to a book.
        
        Args:
            book_id: The ObjectId of the book as string
            changes: Dictionary of changed fields with old/new values
        """
        await self.changes.insert_one({
            'book_id': ObjectId(book_id),
            'changes': changes,
            'timestamp': datetime.utcnow(),
            'change_type': 'update'
        })

    async def get_last_checkpoint(self, checkpoint_type: str = 'page') -> Optional[str]:
        """Get the last successfully processed checkpoint value.
        
        Args:
            checkpoint_type: Type of checkpoint ('page', 'category', etc.)
            
        Returns:
            Optional[str]: The checkpoint value or None if not found
        """
        checkpoint = await self.checkpoints.find_one({'checkpoint_type': checkpoint_type})
        return checkpoint['value'] if checkpoint else None

    async def set_checkpoint(self, value: str, checkpoint_type: str = 'page'):
        """Update the last successfully processed checkpoint.
        
        Args:
            value: The checkpoint value (URL or page number)
            checkpoint_type: Type of checkpoint ('page', 'category', etc.)
        """
        await self.checkpoints.update_one(
            {'checkpoint_type': checkpoint_type},
            {
                '$set': {
                    'value': value,
                    'timestamp': datetime.utcnow()
                }
            },
            upsert=True
        )
        
    async def get_books_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve books by category with optional limit."""
        cursor = self.books.find({'category': category}).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_recent_changes(self, since: datetime) -> List[Dict[str, Any]]:
        """Get all book changes since a given timestamp."""
        cursor = self.changes.find({
            'timestamp': {'$gte': since}
        }).sort('timestamp', -1)
        return await cursor.to_list(length=None)

    async def cleanup_old_snapshots(self, before: datetime):
        """Remove HTML snapshots older than the given date."""
        if settings.store_html_in_gridfs:
            # Find and delete old files in GridFS
            async for grid_out in self.fs.find({
                'uploadDate': {'$lt': before}
            }):
                await self.fs.delete(grid_out._id)
        # Add filesystem cleanup here if needed

    async def __aenter__(self):
        """Support async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting context."""
        self.client.close()

    # Crawl Progress and Recovery Methods
    async def get_crawl_status(self) -> Dict[str, Any]:
        """Get current crawl status for monitoring and resume.
        
        Use case: Track crawl progress and support resume functionality
        Returns:
            - Last successful crawl timestamp
            - Counts by status
            - Last processed URLs
            - Current category progress
        """
        return {
            'last_crawl': await self.books.find_one(
                sort=[('crawl_timestamp', -1)]
            ),
            'status_counts': {
                'success': await self.books.count_documents({'status': 'success'}),
                'error': await self.books.count_documents({'status': 'error'}),
                'pending': await self.books.count_documents({'status': 'pending'})
            },
            'last_checkpoint': await self.get_last_checkpoint(),
            'categories_progress': await self.books.aggregate([
                {'$group': {
                    '_id': '$category',
                    'count': {'$sum': 1},
                    'last_update': {'$max': '$crawl_timestamp'}
                }}
            ]).to_list(None)
        }

    async def get_pending_urls(self, limit: int = 100) -> List[str]:
        """Get URLs that need to be crawled or recrawled.
        
        Use case: Resume interrupted crawls and handle failed requests
        Returns URLs that:
        - Haven't been crawled yet
        - Failed in previous attempts
        - Are marked for recrawl
        """
        cursor = self.books.find({
            'status': {'$in': ['pending', 'error']}
        }, {
            'source_url': 1
        }).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return [doc['source_url'] for doc in docs]

    # Data Quality Methods
    async def find_content_changes(self, book: Book, html: str) -> Dict[str, Any]:
        """Compare new book data with existing record to detect changes.
        
        Use case: Change detection for updates
        Returns dictionary of changed fields with old/new values
        """
        existing = await self.get_book_by_url(book.source_url)
        if not existing:
            return {}
            
        html_hash = await self.compute_html_hash(html)
        if existing.get('raw_html_hash') == html_hash:
            return {}
            
        changes = {
            k: {'old': existing.get(k), 'new': v}
            for k, v in book.model_dump().items()
            if k in existing and existing.get(k) != v
        }
        
        return changes if changes else {}

    # Export and Analysis Methods
    async def get_crawl_metrics(self) -> Dict[str, Any]:
        """Get metrics about the crawl for monitoring.
        
        Use case: Monitor crawl health and performance
        Returns metrics like:
        - Success/failure rates
        - Average response times
        - Category coverage
        """
        return {
            'total_books': await self.books.count_documents({}),
            'error_rate': await self.books.count_documents({'status': 'error'}) / \
                         (await self.books.count_documents({})) * 100,
            'categories': await self.books.distinct('category'),
            'avg_response_time': await self.books.aggregate([
                {'$group': {
                    '_id': None,
                    'avg_time': {'$avg': '$response_time'}
                }}
            ]).to_list(None)
        }

    # Statistics and Monitoring Methods
    async def get_crawl_stats(self) -> Dict[str, Any]:
        """Get crawler statistics for monitoring.
        
        Use case: Monitoring crawl progress and health
        Returns statistics like:
        - Total books crawled
        - Books by category
        - Recent error count
        - Average response times
        """
        stats = {
            'total_books': await self.books.count_documents({}),
            'categories': await self.books.distinct('category'),
            'error_count': await self.books.count_documents({'status': 'error'}),
            'last_crawl': await self.books.find_one(
                sort=[('crawl_timestamp', -1)]
            ),
        }
        return stats

    async def get_failed_books(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get books that failed to crawl properly.
        
        Use case: Error recovery and retry logic
        Returns books with error status or missing required fields.
        """
        cursor = self.books.find({
            '$or': [
                {'status': 'error'},
                {'description': None},
                {'price_incl_tax': 0}
            ]
        }).limit(limit)
        return await cursor.to_list(length=limit)

    # Data Integrity Methods
    async def find_duplicate_books(self) -> List[Dict[str, Any]]:
        """Find potential duplicate books based on title similarity.
        
        Use case: Data cleaning and quality assurance
        Returns books with very similar titles that might be duplicates.
        """
        pipeline = [
            {'$group': {
                '_id': '$title',
                'count': {'$sum': 1},
                'books': {'$push': {
                    'id': '$_id',
                    'url': '$source_url',
                    'category': '$category'
                }}
            }},
            {'$match': {'count': {'$gt': 1}}}
        ]
        return await self.books.aggregate(pipeline).to_list(None)

    # Crawl Management Methods
    async def mark_for_recrawl(self, older_than: datetime) -> int:
        """Mark books for recrawling if they're older than specified.
        
        Use case: Periodic recrawling of old content
        Returns count of books marked for recrawl.
        """
        result = await self.books.update_many(
            {'crawl_timestamp': {'$lt': older_than}},
            {'$set': {'status': 'pending_recrawl'}}
        )
        return result.modified_count

    async def get_category_progress(self, category: str) -> Dict[str, Any]:
        """Get crawl progress for a specific category.
        
        Use case: Category-specific progress monitoring
        Returns statistics about a category's crawl status.
        """
        return {
            'total': await self.books.count_documents({'category': category}),
            'success': await self.books.count_documents({
                'category': category,
                'status': 'success'
            }),
            'error': await self.books.count_documents({
                'category': category,
                'status': 'error'
            }),
            'last_update': await self.books.find_one(
                {'category': category},
                sort=[('crawl_timestamp', -1)]
            )
        }

    # Data Export Methods
    async def get_books_for_export(
        self,
        start_date: datetime,
        end_date: datetime,
        fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get books crawled within a date range for export.
        
        Use case: Data export and reporting
        Returns books with specified fields for external processing.
        """
        projection = {field: 1 for field in (fields or [])} if fields else None
        cursor = self.books.find(
            {
                'crawl_timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            },
            projection
        )
        return await cursor.to_list(None)

    # Cleanup and Maintenance Methods
    async def remove_orphaned_snapshots(self) -> int:
        """Remove HTML snapshots that don't have corresponding books.
        
        Use case: Database maintenance and cleanup
        Returns count of orphaned snapshots removed.
        """
        if not settings.store_html_in_gridfs:
            return 0
            
        removed = 0
        async for grid_out in self.fs.find():
            book_id = grid_out.metadata.get('book_id')
            if book_id and not await self.books.find_one({'_id': ObjectId(book_id)}):
                await self.fs.delete(grid_out._id)
                removed += 1
        return removed

    async def consolidate_changes(self, older_than: datetime) -> int:
        """Consolidate old change records into summary records.
        
        Use case: Database optimization and storage management
        Returns count of consolidated change records.
        """
        pipeline = [
            {'$match': {'timestamp': {'$lt': older_than}}},
            {'$group': {
                '_id': '$book_id',
                'change_count': {'$sum': 1},
                'first_change': {'$min': '$timestamp'},
                'last_change': {'$max': '$timestamp'}
            }}
        ]
        
        consolidated = 0
        async for summary in self.changes.aggregate(pipeline):
            await self.changes.delete_many({
                'book_id': summary['_id'],
                'timestamp': {'$lt': older_than}
            })
            await self.changes.insert_one({
                'book_id': summary['_id'],
                'change_type': 'consolidated',
                'timestamp': datetime.utcnow(),
                'summary': {
                    'change_count': summary['change_count'],
                    'date_range': [summary['first_change'], summary['last_change']]
                }
            })
            consolidated += 1
        
        return consolidated