# scheduler/notifications.py

"""
Notification system for book changes and system alerts.
Simulates email sending through logging for development and testing.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import json
from pydantic import BaseModel, Field

from src.crawler.settings import Settings

logger = logging.getLogger('scheduler.notifications')

class EmailConfig(BaseModel):
    """Email configuration settings."""
    sender_email: str = Field("bookstore-alerts@example.com", description="Sender email address")
    admin_email: str = Field("admin@example.com", description="Admin email for system alerts")
    notification_level: str = Field("all", description="Notification level: all, important, critical")
    simulate: bool = Field(True, description="If True, log emails instead of sending")


class NotificationManager:
    """Manages notifications for book changes and system events."""
    
    def __init__(self):
        """Initialize notification manager with settings."""
        self.settings = Settings()
        self.email_config = EmailConfig()
        
        # Configure notification logger first
        self._setup_notification_logger()
        
        # Load email templates
        self._load_templates()
    
    def _load_templates(self):
        """Load email templates from templates directory."""
        # In memory default templates for testing
        self.templates = {
            'price_change.html': '''
<h2>Book Price Change Alert</h2>
<p>The following book has had a significant price change:</p>
<ul>
    <li>Title: {book_title}</li>
    <li>Previous Price: {old_price}</li>
    <li>New Price: {new_price}</li>
    <li>Change Percentage: {change_percentage}%</li>
</ul>
<p>View more details in the daily report.</p>
''',
            'availability_change.html': '''
<h2>Book Availability Change Alert</h2>
<p>The following book has had an availability change:</p>
<ul>
    <li>Title: {book_title}</li>
    <li>Previous Status: {old_status}</li>
    <li>New Status: {new_status}</li>
</ul>
<p>View more details in the daily report.</p>
''',
            'error_alert.html': '''
<h2>System Error Alert</h2>
<p>An error has occurred in the book monitoring system:</p>
<ul>
    <li>Component: {component}</li>
    <li>Error Type: {error_type}</li>
    <li>Timestamp: {timestamp}</li>
</ul>
<p>Error Details:</p>
<pre>{error_details}</pre>
'''
        }
    
    def _create_default_templates(self, template_dir: Path):
        """Create default email templates if they don't exist."""
        default_templates = {
            'price_change.html': '''
<h2>Book Price Change Alert</h2>
<p>The following book has had a significant price change:</p>
<ul>
    <li>Title: {book_title}</li>
    <li>Previous Price: {old_price}</li>
    <li>New Price: {new_price}</li>
    <li>Change Percentage: {change_percentage}%</li>
</ul>
<p>View more details in the daily report.</p>
''',
            'availability_change.html': '''
<h2>Book Availability Change Alert</h2>
<p>The following book has had an availability change:</p>
<ul>
    <li>Title: {book_title}</li>
    <li>Previous Status: {old_status}</li>
    <li>New Status: {new_status}</li>
</ul>
<p>View more details in the daily report.</p>
''',
            'new_book.html': '''
<h2>New Book Alert</h2>
<p>A new book has been added to the catalog:</p>
<ul>
    <li>Title: {book_title}</li>
    <li>Author: {author}</li>
    <li>Price: {price}</li>
    <li>Category: {category}</li>
</ul>
''',
            'error_alert.html': '''
<h2>System Error Alert</h2>
<p>An error has occurred in the book monitoring system:</p>
<ul>
    <li>Component: {component}</li>
    <li>Error Type: {error_type}</li>
    <li>Timestamp: {timestamp}</li>
</ul>
<p>Error Details:</p>
<pre>{error_details}</pre>
'''
        }
        
        for name, content in default_templates.items():
            template_path = template_dir / name
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _setup_notification_logger(self):
        """Set up a dedicated logger for notification simulation."""
        notifications_log = logging.FileHandler('logs/notifications.log')
        notifications_log.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(levelname)s - NOTIFICATION:\n%(message)s\n'
            )
        )
        
        notification_logger = logging.getLogger('notifications')
        notification_logger.addHandler(notifications_log)
        notification_logger.setLevel(logging.INFO)
        self.notification_logger = notification_logger
    
    def _simulate_email(self, subject: str, body: str, recipients: List[str]):
        """Simulate sending an email by logging it."""
        email_content = (
            f"{'='*50}\n"
            f"To: {', '.join(recipients)}\n"
            f"Subject: {subject}\n"
            f"{'='*50}\n\n"
            f"{body}\n"
            f"{'='*50}"
        )
        self.notification_logger.info(email_content)
    
    async def notify_price_change(
        self,
        book_id: str,
        book_title: str,
        old_price: float,
        new_price: float
    ):
        """Notify about significant price changes."""
        change_pct = ((new_price - old_price) / old_price) * 100
        
        # Only notify for significant changes (>20%)
        if abs(change_pct) >= 20:
            context = {
                'book_title': book_title,
                'old_price': f"${old_price:.2f}",
                'new_price': f"${new_price:.2f}",
                'change_percentage': f"{change_pct:.1f}"
            }
            
            body = self.templates['price_change.html'].format(**context)
            subject = f"Price Alert: {book_title} price changed by {change_pct:.1f}%"
            
            self._simulate_email(
                subject,
                body,
                [self.email_config.admin_email]
            )
    
    async def notify_availability_change(
        self,
        book_id: str,
        book_title: str,
        old_status: str,
        new_status: str
    ):
        """Notify about availability changes."""
        if old_status == 'in_stock' and new_status == 'out_of_stock':
            context = {
                'book_title': book_title,
                'old_status': old_status,
                'new_status': new_status
            }
            
            body = self.templates['availability_change.html'].format(**context)
            subject = f"Availability Alert: {book_title} is now out of stock"
            
            self._simulate_email(
                subject,
                body,
                [self.email_config.admin_email]
            )
    
    async def notify_new_book(self, book_data: Dict[str, Any]):
        """Notify about new books added to the catalog."""
        if self.email_config.notification_level in ['all']:
            context = {
                'book_title': book_data.get('title', 'Unknown Title'),
                'author': book_data.get('author', 'Unknown Author'),
                'price': f"${book_data.get('price', 0.0):.2f}",
                'category': book_data.get('category', 'Uncategorized')
            }
            
            body = self.templates['new_book.html'].format(**context)
            subject = f"New Book Added: {context['book_title']}"
            
            self._simulate_email(
                subject,
                body,
                [self.email_config.admin_email]
            )
    
    async def notify_error(
        self,
        component: str,
        error_type: str,
        error_details: str,
        critical: bool = False
    ):
        """Notify about system errors."""
        if critical or self.email_config.notification_level in ['all', 'important']:
            context = {
                'component': component,
                'error_type': error_type,
                'timestamp': datetime.utcnow().isoformat(),
                'error_details': error_details
            }
            
            body = self.templates['error_alert.html'].format(**context)
            subject = f"{'CRITICAL ' if critical else ''}Error in {component}: {error_type}"
            
            self._simulate_email(
                subject,
                body,
                [self.email_config.admin_email]
            )
    
    async def send_daily_summary(self, report_data: Dict[str, Any]):
        """Send daily summary of changes and system status."""
        if self.email_config.notification_level in ['all']:
            # Create a simple HTML summary
            summary = []
            summary.append("<h2>Daily Book Monitoring Summary</h2>")
            summary.append(f"<p>Date: {report_data['date']}</p>")
            summary.append(f"<p>Total Changes: {report_data['total_changes']}</p>")
            
            for change_type, data in report_data['changes_by_type'].items():
                summary.append(f"<h3>{change_type} Changes</h3>")
                summary.append(f"<p>Count: {data['count']}</p>")
            
            body = "\n".join(summary)
            subject = f"Daily Summary Report - {report_data['date']}"
            
            self._simulate_email(
                subject,
                body,
                [self.email_config.admin_email]
            )