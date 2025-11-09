# scheduler/reporting.py

"""
Change reporting system for tracking and analyzing book changes.
Integrates with existing crawler and scheduler components.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from crawler.settings import Settings
from .models import ChangeRecord
from .notifications import NotificationManager

logger = logging.getLogger('scheduler.reporting')

class ChangeReporter:
    """Handles change tracking, reporting, and notifications."""
    
    def __init__(self, db_client: Optional[AsyncIOMotorClient] = None):
        """Initialize reporter with database connection."""
        self.settings = Settings()
        self.db_client = db_client or AsyncIOMotorClient(self.settings.mongo_uri)
        # Extract database name from mongo_uri
        self.db = self.db_client.get_database()
        self.notifications = NotificationManager()
        
        # Create reports directory if it doesn't exist
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def record_change(self, book_id: str, changes: Dict[str, Any]) -> str:
        """
        Record a book change in the database.
        
        Args:
            book_id: ID of the book that changed
            changes: Dictionary containing changes with structure:
                {field: {'old': old_value, 'new': new_value}}
        
        Returns:
            ID of the created change record
        """
        change_record = ChangeRecord(
            book_id=ObjectId(book_id),
            timestamp=datetime.utcnow(),
            changes=changes
        )
        
        result = await self.db.change_records.insert_one(change_record.model_dump())
        
        # If this is a significant change, trigger immediate notification
        if self._is_significant_change(changes):
            # Get book details for notification
            book = await self.store.books.find_one({"_id": ObjectId(book_id)})
            if book:
                if 'price' in changes:
                    await self.notifications.notify_price_change(
                        str(book['_id']),
                        book['title'],
                        float(changes['price']['old']),
                        float(changes['price']['new'])
                    )
        
        return str(result.inserted_id)
    
    def _is_significant_change(self, changes: Dict[str, Any]) -> bool:
        """Determine if a change requires immediate notification."""
        if 'price' in changes:
            old_price = float(changes['price']['old'])
            new_price = float(changes['price']['new'])
            change_pct = abs((new_price - old_price) / old_price * 100)
            return change_pct >= 20
        return False
        significant_conditions = [
            # Price changes over 20%
            lambda c: (
                c.get('field') == 'price' and
                c.get('old_value') and
                c.get('new_value') and
                abs((float(c['new_value']) - float(c['old_value'])) / float(c['old_value'])) > 0.2
            ),
            # Availability changes from in stock to out of stock
            lambda c: (
                c.get('field') == 'availability' and
                c.get('old_value') == 'in_stock' and
                c.get('new_value') == 'out_of_stock'
            )
        ]
        
        return any(condition(changes) for condition in significant_conditions)
    
    async def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate a daily summary report of all changes."""
        date = date or datetime.utcnow()
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Get all change records for the day
        changes = await self.db.change_records.find({
            'timestamp': {
                '$gte': start_date,
                '$lt': end_date
            }
        }).to_list(None)
        
        # Process changes to extract field-level details
        changes_by_type = {}
        total_changes = 0
        
        for change_record in changes:
            book_id = change_record['book_id']
            
            # Get book details
            book = await self.db.books.find_one({'_id': book_id})
            book_title = book['title'] if book else 'Unknown'
            
            # Process each field change in the changes dict
            for field, change_data in change_record['changes'].items():
                if field not in changes_by_type:
                    changes_by_type[field] = {
                        'count': 0,
                        'details': []
                    }
                
                changes_by_type[field]['count'] += 1
                changes_by_type[field]['details'].append({
                    'book_title': book_title,
                    'book_id': book_id,
                    'old_value': change_data.get('old'),
                    'new_value': change_data.get('new'),
                    'timestamp': change_record['timestamp']
                })
                total_changes += 1
        
        # Generate report
        report = {
            'date': start_date.date().isoformat(),
            'total_changes': total_changes,
            'changes_by_type': changes_by_type
        }
        
        # Save report files
        await self._save_report_files(report, start_date)
        
        return report
    
    async def _save_report_files(self, report: Dict[str, Any], date: datetime):
        """Save report in both JSON and CSV formats."""
        date_str = date.strftime('%Y-%m-%d')
        
        # Save JSON report
        json_path = self.reports_dir / f'change_report_{date_str}.json'
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save CSV report
        csv_path = self.reports_dir / f'change_report_{date_str}.csv'
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Change Type', 'Book Title', 'Old Value', 'New Value', 'Timestamp'])
            
            for change_type, data in report['changes_by_type'].items():
                for change in data['details']:
                    writer.writerow([
                        date_str,
                        change_type,
                        change['book_title'],
                        change['old_value'],
                        change['new_value'],
                        change['timestamp']
                    ])
    
    async def get_change_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistical analysis of changes over a period."""
        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=30))
        
        pipeline = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                        'field': '$changes.field'
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$group': {
                    '_id': '$_id.field',
                    'daily_counts': {
                        '$push': {
                            'date': '$_id.date',
                            'count': '$count'
                        }
                    },
                    'total_count': {'$sum': '$count'},
                    'avg_daily_changes': {'$avg': '$count'}
                }
            }
        ]
        
        results = await self.db.change_records.aggregate(pipeline).to_list(None)
        
        return {
            'period_start': start_date.date().isoformat(),
            'period_end': end_date.date().isoformat(),
            'statistics_by_type': {
                r['_id']: {
                    'total_changes': r['total_count'],
                    'avg_daily_changes': round(r['avg_daily_changes'], 2),
                    'daily_breakdown': r['daily_counts']
                }
                for r in results
            }
        }
    
    async def _send_alert(self, book_id: str, changes: Dict[str, Any]):
        """Send immediate alert for significant changes."""
        book = await self.db.books.find_one({'_id': ObjectId(book_id)})
        if not book:
            return
        
        alert = {
            'timestamp': datetime.utcnow(),
            'book_id': book_id,
            'book_title': book['title'],
            'change_type': changes['field'],
            'old_value': changes['old_value'],
            'new_value': changes['new_value'],
            'alert_type': 'significant_change'
        }
        
        # Store alert in database
        await self.db.alerts.insert_one(alert)
        
        # Send notifications based on change type
        if changes['field'] == 'price':
            await self.notifications.notify_price_change(
                book_id,
                book['title'],
                float(changes['old_value']),
                float(changes['new_value'])
            )
        elif changes['field'] == 'availability':
            await self.notifications.notify_availability_change(
                book_id,
                book['title'],
                changes['old_value'],
                changes['new_value']
            )
        
        # Log the alert
        logger.warning(
            f"Significant change detected for book '{book['title']}': "
            f"{changes['field']} changed from {changes['old_value']} to {changes['new_value']}"
        )