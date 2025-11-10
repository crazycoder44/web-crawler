# scheduler/change_tracker.py

"""
Change tracking system for monitoring book updates.
Integrates with the crawler's existing MongoStore for change detection and recording.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

from src.crawler.store import MongoStore
from src.crawler.models import Book
from .fingerprinting import detect_changes, is_significant_change, summarize_changes
from .models import BookChange, DailyChangeReport, ConsolidatedChanges

logger = logging.getLogger('scheduler')


class BookChangeTracker:
    """Tracks and records changes in book data using crawler's MongoStore."""
    
    def __init__(self):
        """Initialize the change tracker using crawler's store."""
        self.store = MongoStore()
        
    async def __aenter__(self):
        """Support async context manager."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting context."""
        await self.store.client.close()
    
    async def process_book_update(self, book: Book, html: str) -> Optional[BookChange]:
        """
        Process and record changes for a single book.
        
        Args:
            book: Book model instance with new data
            html: Raw HTML content of the book page
            
        Returns:
            Optional[BookChange]: Change record if changes detected, None otherwise
        """
        # Use crawler's content change detection
        changes = await self.store.find_content_changes(book, html)
        
        if not changes:
            return None
            
        # Create and store change record
        change = BookChange(
            book_id=book.id,
            changes=changes,
            change_type='update'
        )
        
        # Store the change using crawler's collection
        await self.store.record_change(book.id, changes)
        
        # Log significant changes
        if is_significant_change(changes):
            logger.info(f"Significant changes detected for book {book.id}: {changes}")
            
        return change
    
    async def get_daily_changes(self, date: datetime) -> DailyChangeReport:
        """
        Get a report of all changes for a specific date.
        
        Args:
            date: Date to get changes for
            
        Returns:
            DailyChangeReport: Report of changes
        """
        start_of_day = datetime(date.year, date.month, date.day)
        end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)
        
        # Get changes using crawler's store
        changes = await self.store.get_recent_changes(start_of_day)
        
        # Get crawl metrics
        metrics = await self.store.get_crawl_metrics()
        
        # Filter changes for the day
        day_changes = [
            change for change in changes
            if start_of_day <= change['timestamp'] <= end_of_day
        ]
        
        # Count new books (those without previous versions)
        new_books = len([
            change for change in day_changes
            if not change.get('changes')  # No previous version
        ])
        
        # Create summary
        report = DailyChangeReport(
            date=date,
            total_books=metrics['total_books'],
            new_books=new_books,
            updated_books=len(day_changes) - new_books,
            changes_by_type=self._summarize_changes(day_changes),
            error_count=int(metrics['total_books'] * metrics['error_rate'] / 100),
            metrics={
                'avg_response_time': metrics['avg_response_time'][0]['avg_time']
                if metrics['avg_response_time'] else None,
                'categories': len(metrics['categories'])
            }
        )
        
        return report
    
    def _summarize_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Create a summary of changes by type.
        
        Args:
            changes: List of change records
            
        Returns:
            Dict[str, int]: Count of each type of change
        """
        summary = {}
        for change in changes:
            if 'changes' in change:
                for field in change['changes']:
                    summary[field] = summary.get(field, 0) + 1
        return summary
    
    async def consolidate_old_changes(self, days_threshold: int = 30) -> None:
        """
        Consolidate old change records to optimize storage.
        
        Args:
            days_threshold: Age in days after which to consolidate changes
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        await self.store.consolidate_changes(cutoff_date)