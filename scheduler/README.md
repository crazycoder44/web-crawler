# Web Crawler Scheduler Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Jobs](#jobs)
5. [Email Templates](#email-templates)
6. [Setup and Configuration](#setup-and-configuration)
7. [Usage](#usage)
8. [Error Handling](#error-handling)
9. [Monitoring](#monitoring)

## Overview

The scheduler is a comprehensive automated task management system that orchestrates periodic web crawling, change detection, maintenance, and health monitoring operations. Built on top of APScheduler, it provides robust job scheduling with error handling, retry logic, and notification capabilities.

### Key Features
- **Automated Crawling**: Schedules full site scans at optimal times
- **Change Detection**: Monitors books for price, availability, and content changes
- **Smart Notifications**: Email alerts for significant changes
- **Maintenance Tasks**: Automatic cleanup and optimization
- **Health Monitoring**: Continuous system health checks
- **Retry Logic**: Automatic retry on failures with exponential backoff
- **Event Tracking**: Comprehensive logging and database records

## Architecture

```
scheduler/
├── scheduler.py          # Main scheduler orchestration
├── jobs.py              # Job implementations
├── change_tracker.py    # Change detection system
├── fingerprinting.py    # Content fingerprinting utilities
├── notifications.py     # Email notification manager
├── reporting.py         # Report generation
├── db_setup.py         # Database initialization
├── models.py           # Data models
├── config.py           # Configuration management
├── settings.py         # Settings and constants
├── logging_config.py   # Logging configuration
└── templates/          # Email templates
    ├── price_change.html
    ├── availability_change.html
    ├── new_book.html
    └── error_alert.html
```

### Data Flow
1. **Scheduler** triggers jobs based on cron expressions
2. **Jobs** execute crawler operations and collect data
3. **Change Tracker** compares current vs. previous data
4. **Fingerprinting** generates content signatures for comparison
5. **Notifications** send email alerts for significant changes
6. **Reporting** generates daily/weekly summaries
7. **Database** stores all results, changes, and job history

## Components

### 1. scheduler.py - Main Scheduler

The `BookScheduler` class is the central orchestrator that manages all scheduled jobs.

**Key Features:**
- Initializes APScheduler with AsyncIO event loop support
- Configures job triggers (cron expressions)
- Handles job events (success/failure)
- Manages job lifecycle and error recovery

**Configuration Options:**
```python
scheduler = BookScheduler()
```

**Job Configuration Parameters:**
- `coalesce`: Prevents multiple missed jobs from running simultaneously
- `max_instances`: Limits concurrent job executions
- `misfire_grace_time`: Time window for delayed execution before skipping

### 2. jobs.py - Job Implementations

Contains four main scheduled jobs:

#### a. Full Site Scan Job
**Purpose**: Complete crawl of all books across all categories

**Schedule**: Daily at 2:00 AM  
**Trigger**: `CronTrigger(hour=2, minute=0)`

**Features:**
- Initializes BooksCrawler with checkpoint support
- Retry logic: Up to 3 attempts with exponential backoff
- Records statistics: books processed, categories, errors
- Stores results in MongoDB

**Error Handling:**
- Automatic retry on network failures
- Exponential backoff: 1s, 2s, 4s
- Final failure notification via email

**Expected Results:**
```python
{
    'total_books': 1000,
    'categories_processed': 50,
    'failed_urls': 0,
    'duration_seconds': 264.31,
    'successful': True
}
```

#### b. Change Detection Job
**Purpose**: Detect changes in book data without full crawl

**Schedule**: Every 4 hours  
**Trigger**: `CronTrigger(hour='*/4')`

**Detection Types:**
- **Price Changes**: Monitors price increases/decreases
- **Availability Changes**: Tracks stock status (In Stock ↔ Out of Stock)
- **Content Changes**: Detects description modifications
- **New Books**: Identifies newly added books

**Thresholds:**
- Significant price change: ≥10% or ≥$5
- Significant content change: ≥20% text difference

**Process:**
1. Query recent books (last 24 hours)
2. Re-crawl book pages
3. Compare with stored data using fingerprints
4. Record changes in database
5. Send notifications for significant changes

#### c. Maintenance Job
**Purpose**: Database cleanup and optimization

**Schedule**: Daily at 3:00 AM  
**Trigger**: `CronTrigger(hour=3, minute=0)`

**Tasks:**
- Remove old job history (>90 days)
- Archive old change records (>180 days)
- Cleanup orphaned checkpoint data
- Optimize database indexes
- Generate daily reports

**Cleanup Thresholds:**
```python
{
    'job_history_retention': 90,    # days
    'change_records_retention': 180, # days
    'checkpoint_retention': 30       # days
}
```

#### d. Health Check Job
**Purpose**: Monitor system health and availability

**Schedule**: Every 15 minutes  
**Trigger**: `CronTrigger(minute='*/15')`

**Checks:**
- Database connectivity (MongoDB)
- Target website availability
- Scheduler job status
- System resource usage
- Last successful job execution times

**Alert Conditions:**
- Database connection failure
- Website unreachable for >30 minutes
- No successful full scan in >48 hours
- High error rate (>10% in last hour)

### 3. change_tracker.py - Change Detection

The `BookChangeTracker` class implements intelligent change detection.

**Core Methods:**

#### `process_book_update(book: Book, html: str)`
Processes a single book update and detects changes.

**Parameters:**
- `book`: Book model with new data
- `html`: Raw HTML content

**Returns:**
- `BookChange` object if changes detected
- `None` if no significant changes

**Detection Algorithm:**
1. Generate fingerprint of new content
2. Retrieve previous fingerprint from database
3. Compare fingerprints for differences
4. Calculate change significance
5. Create change record if threshold exceeded

#### `detect_changes_batch(books: List[Book], days: int = 1)`
Batch process multiple books for change detection.

**Performance:**
- Concurrent processing of up to 10 books
- Average processing time: 2-3 seconds per book
- Uses connection pooling for efficiency

**Output:**
```python
{
    'total_checked': 100,
    'changes_detected': 15,
    'price_changes': 8,
    'availability_changes': 5,
    'content_changes': 2
}
```

### 4. fingerprinting.py - Content Fingerprinting

Generates unique signatures for book content to enable efficient change detection.

**Functions:**

#### `generate_fingerprint(book: Book, html: str) -> str`
Creates a SHA-256 hash of normalized book content.

**Includes:**
- Title (normalized)
- Price (rounded to 2 decimals)
- Availability status
- Description text (cleaned, lowercased)
- Rating

**Example:**
```python
fingerprint = "a1b2c3d4e5f6..."  # 64-character hex string
```

#### `detect_changes(old_fp: str, new_fp: str, old_book: Book, new_book: Book) -> List[str]`
Compares fingerprints and identifies specific changes.

**Returns List of Changes:**
```python
['price', 'availability', 'description']
```

#### `is_significant_change(changes: List[str], old_book: Book, new_book: Book) -> bool`
Determines if changes warrant notification.

**Significance Criteria:**
- Price change ≥10% or ≥$5.00
- Availability status change
- Description change ≥20% of content

### 5. notifications.py - Email Notifications

The `NotificationManager` class handles email alerts.

**Configuration:**
```python
# Required environment variables
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USERNAME = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_FROM = "Web Crawler <noreply@crawler.com>"
EMAIL_TO = ["admin@example.com"]
```

**Methods:**

#### `send_change_alert(change: BookChange, template: str)`
Sends email for a specific change type.

**Templates:**
- `price_change.html`: Price increase/decrease
- `availability_change.html`: Stock status change
- `new_book.html`: New book discovered
- `error_alert.html`: System errors

**Rate Limiting:**
- Max 100 emails per hour
- Batches multiple changes when possible
- Deduplicates notifications

#### `send_daily_report(report: DailyChangeReport)`
Sends comprehensive daily summary.

**Includes:**
- Total changes by type
- Top price changes
- New books added
- Availability updates
- Error summary

### 6. reporting.py - Report Generation

The `ChangeReporter` class generates analytical reports.

**Report Types:**

#### Daily Change Report
Generated after each full scan or change detection.

**Contents:**
```python
{
    'date': '2025-11-09',
    'total_changes': 45,
    'price_changes': 20,
    'availability_changes': 15,
    'content_changes': 10,
    'new_books': 5,
    'top_price_increases': [...],
    'top_price_decreases': [...],
    'newly_available': [...],
    'newly_unavailable': [...]
}
```

#### Weekly Trend Report
Aggregates weekly statistics.

**Includes:**
- Change trends over time
- Average price changes
- Most volatile books
- Category-level statistics

#### Custom Reports
Generate ad-hoc reports using:
```python
reporter.generate_custom_report(
    start_date='2025-11-01',
    end_date='2025-11-07',
    filters={'category': 'Fiction'}
)
```

### 7. db_setup.py - Database Setup

The `SchedulerStore` class manages scheduler-specific database operations.

**Collections:**

#### `scheduler_runs`
Records job execution history.

**Schema:**
```python
{
    '_id': ObjectId,
    'job_id': 'full_site_scan',
    'status': 'success',  # 'running', 'success', 'error'
    'start_time': datetime,
    'end_time': datetime,
    'attempts': 2,
    'metadata': {...}
}
```

#### `book_changes`
Stores detected changes.

**Schema:**
```python
{
    '_id': ObjectId,
    'book_id': ObjectId,
    'timestamp': datetime,
    'change_type': 'price',  # 'price', 'availability', 'content'
    'old_value': '29.99',
    'new_value': '24.99',
    'change_percentage': -16.67,
    'significant': True
}
```

#### `health_checks`
Monitors system health.

**Schema:**
```python
{
    '_id': ObjectId,
    'timestamp': datetime,
    'database_status': 'healthy',
    'website_status': 'healthy',
    'last_successful_scan': datetime,
    'error_rate': 0.02
}
```

**Initialization:**
```python
store = SchedulerStore()
await store.init_collections()
```

### 8. models.py - Data Models

Pydantic models for type safety and validation.

**Models:**

#### `BookChange`
```python
class BookChange(BaseModel):
    book_id: str
    title: str
    change_type: str  # 'price', 'availability', 'content', 'new'
    timestamp: datetime
    old_value: Optional[str]
    new_value: Optional[str]
    change_percentage: Optional[float]
    significant: bool
```

#### `DailyChangeReport`
```python
class DailyChangeReport(BaseModel):
    date: str
    total_changes: int
    price_changes: int
    availability_changes: int
    content_changes: int
    new_books: int
    changes: List[BookChange]
    statistics: Dict[str, Any]
```

#### `ConsolidatedChanges`
```python
class ConsolidatedChanges(BaseModel):
    price_changes: List[BookChange]
    availability_changes: List[BookChange]
    content_changes: List[BookChange]
    new_books: List[BookChange]
    total_count: int
```

## Email Templates

Email templates use Jinja2 templating for dynamic content.

### 1. price_change.html

**Purpose**: Alert for significant price changes

**Variables:**
- `book_title`: Book name
- `old_price`: Previous price
- `new_price`: Current price
- `change_percentage`: % change (positive/negative)
- `url`: Book detail page URL

**Example Output:**
```
Book Price Change Alert

The following book has had a significant price change:
- Title: The Great Gatsby
- Previous Price: $29.99
- New Price: $24.99
- Change Percentage: -16.7%

View more details in the daily report.
```

### 2. availability_change.html

**Purpose**: Alert for stock status changes

**Variables:**
- `book_title`: Book name
- `old_availability`: Previous status
- `new_availability`: Current status
- `price`: Current price
- `url`: Book detail page URL

**Use Cases:**
- Out of Stock → In Stock (buying opportunity)
- In Stock → Out of Stock (scarcity alert)

### 3. new_book.html

**Purpose**: Notification for newly discovered books

**Variables:**
- `book_title`: Book name
- `category`: Book category
- `price`: Current price
- `rating`: Star rating
- `description`: Book description snippet
- `url`: Book detail page URL

**Triggered When:**
- Book not in database
- New category discovered
- Previously missing data now available

### 4. error_alert.html

**Purpose**: System error notifications

**Variables:**
- `job_id`: Failed job name
- `error_message`: Error description
- `timestamp`: Error occurrence time
- `attempts`: Number of retry attempts
- `next_retry`: Scheduled retry time (if applicable)

**Severity Levels:**
- **Warning**: Single failure (auto-retry)
- **Error**: Multiple failures (manual intervention needed)
- **Critical**: System-wide issues (immediate action required)

## Setup and Configuration

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- SMTP server access (Gmail, SendGrid, etc.)

### Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

Required packages:
- APScheduler
- motor (async MongoDB)
- jinja2 (templating)
- aiosmtplib (async email)

2. **Environment Variables**

Create `.env` file:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=books_crawler

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=Web Crawler <noreply@crawler.com>
EMAIL_TO=admin@example.com,alerts@example.com

# Scheduler Settings
FULL_SCAN_HOUR=2
FULL_SCAN_MINUTE=0
CHANGE_DETECTION_INTERVAL=4
MAINTENANCE_HOUR=3
HEALTH_CHECK_INTERVAL=15

# Notification Settings
MAX_EMAILS_PER_HOUR=100
BATCH_NOTIFICATIONS=true
SIGNIFICANT_PRICE_CHANGE_PERCENT=10
SIGNIFICANT_PRICE_CHANGE_AMOUNT=5
```

3. **Database Initialization**

```python
from scheduler.db_setup import init_scheduler_db

# Initialize collections and indexes
await init_scheduler_db()
```

4. **Template Configuration**

Templates are auto-loaded from `scheduler/templates/`. To customize:
```python
# Edit templates in scheduler/templates/
# No code changes needed - changes take effect immediately
```

### Configuration Options

Edit `scheduler/config.py`:

```python
class SchedulerConfig:
    # Job Schedules
    FULL_SCAN_SCHEDULE = {'hour': 2, 'minute': 0}
    CHANGE_DETECTION_SCHEDULE = {'hour': '*/4'}
    MAINTENANCE_SCHEDULE = {'hour': 3, 'minute': 0}
    HEALTH_CHECK_SCHEDULE = {'minute': '*/15'}
    
    # Retry Settings
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1  # seconds
    MAX_RETRY_DELAY = 60     # seconds
    
    # Change Detection
    SIGNIFICANT_PRICE_CHANGE_PERCENT = 10
    SIGNIFICANT_PRICE_CHANGE_AMOUNT = 5.0
    SIGNIFICANT_CONTENT_CHANGE_PERCENT = 20
    
    # Maintenance
    JOB_HISTORY_RETENTION_DAYS = 90
    CHANGE_RECORDS_RETENTION_DAYS = 180
    CHECKPOINT_RETENTION_DAYS = 30
    
    # Health Checks
    WEBSITE_TIMEOUT = 30  # seconds
    MAX_ALLOWED_ERROR_RATE = 0.10  # 10%
    SCAN_STALENESS_HOURS = 48
```

## Usage

### Starting the Scheduler

**Basic Usage:**
```python
import asyncio
from scheduler.scheduler import BookScheduler

async def main():
    scheduler = BookScheduler()
    await scheduler.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await scheduler.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

**With Custom Configuration:**
```python
from scheduler.scheduler import BookScheduler
from scheduler.config import SchedulerConfig

# Customize config
config = SchedulerConfig()
config.FULL_SCAN_SCHEDULE = {'hour': 1, 'minute': 30}
config.MAX_RETRIES = 5

# Initialize with config
scheduler = BookScheduler(config=config)
await scheduler.start()
```

### Manual Job Execution

Execute jobs on-demand:

```python
from scheduler.jobs import SchedulerJobs

jobs = SchedulerJobs()

# Run full site scan
stats = await jobs.full_site_scan()
print(f"Scanned {stats['total_books']} books")

# Run change detection
changes = await jobs.detect_changes()
print(f"Detected {changes['total_changes']} changes")

# Run maintenance
cleanup_stats = await jobs.maintenance()
print(f"Removed {cleanup_stats['records_deleted']} old records")

# Run health check
health = await jobs.health_check()
print(f"System status: {health['status']}")
```

### Viewing Job Status

```python
from scheduler.db_setup import SchedulerStore

store = SchedulerStore()

# Get recent job runs
recent_runs = await store.get_recent_runs(job_id='full_site_scan', limit=10)
for run in recent_runs:
    print(f"{run['start_time']}: {run['status']}")

# Get job statistics
stats = await store.get_job_statistics('full_site_scan', days=30)
print(f"Success rate: {stats['success_rate']}%")
print(f"Average duration: {stats['avg_duration']} seconds")
```

### Querying Changes

```python
from scheduler.change_tracker import BookChangeTracker
from datetime import datetime, timedelta

tracker = BookChangeTracker()

# Get recent price changes
price_changes = await tracker.get_changes(
    change_type='price',
    start_date=datetime.utcnow() - timedelta(days=7),
    significant_only=True
)

# Get changes for specific book
book_history = await tracker.get_book_history(book_id='60f1b2c3...')

# Get daily summary
daily_summary = await tracker.get_daily_summary(date='2025-11-09')
```

### Generating Reports

```python
from scheduler.reporting import ChangeReporter

reporter = ChangeReporter()

# Generate daily report
daily_report = await reporter.generate_daily_report()

# Generate weekly trends
weekly_report = await reporter.generate_weekly_report()

# Export to file
await reporter.export_report(daily_report, format='json', path='reports/')
await reporter.export_report(daily_report, format='csv', path='reports/')
```

## Error Handling

### Retry Mechanism

Jobs automatically retry on failure with exponential backoff:

```python
# Attempt 1: Immediate
# Attempt 2: Wait 1 second
# Attempt 3: Wait 2 seconds
# Attempt 4: Wait 4 seconds (max retries reached)
```

### Error Logging

All errors are logged at multiple levels:

**Console Output:**
```
2025-11-09 02:00:00 ERROR - Job full_site_scan failed: Connection timeout
2025-11-09 02:00:01 INFO  - Retrying in 1 seconds (attempt 1/3)
```

**Database Records:**
```python
{
    'job_id': 'full_site_scan',
    'status': 'error',
    'error_message': 'Connection timeout',
    'attempt': 1,
    'timestamp': datetime(2025, 11, 9, 2, 0, 0)
}
```

**Email Alerts:**
Sent for:
- All retries exhausted
- Critical system failures
- High error rates
- Health check failures

### Recovery Procedures

**Database Connection Loss:**
1. Scheduler pauses all jobs
2. Attempts reconnection every 60 seconds
3. Resumes jobs after successful reconnection
4. No data loss (uses checkpoints)

**Website Unavailability:**
1. Job fails with timeout
2. Retries with backoff
3. If persistent, sends alert email
4. Next scheduled run attempts normally

**Corrupted Data:**
1. Validation catches invalid data
2. Logs error with book details
3. Continues with next book
4. Reports errors in daily summary

## Monitoring

### Health Dashboard

Query health metrics:

```python
from scheduler.db_setup import SchedulerStore

store = SchedulerStore()

# Current health status
health = await store.get_latest_health_check()
print(f"Database: {health['database_status']}")
print(f"Website: {health['website_status']}")
print(f"Error rate: {health['error_rate']}%")

# Health history
history = await store.get_health_history(days=7)
```

### Performance Metrics

```python
# Job execution times
metrics = await store.get_job_metrics('full_site_scan', days=30)
print(f"Average duration: {metrics['avg_duration']}s")
print(f"Min duration: {metrics['min_duration']}s")
print(f"Max duration: {metrics['max_duration']}s")

# Success rates
rates = await store.get_success_rates(days=30)
print(f"Full scan: {rates['full_site_scan']}%")
print(f"Change detection: {rates['change_detection']}%")
```

### Change Statistics

```python
# Changes over time
stats = await tracker.get_change_statistics(days=30)
print(f"Total changes: {stats['total']}")
print(f"Price changes: {stats['price']} ({stats['price_percent']}%)")
print(f"Availability: {stats['availability']} ({stats['availability_percent']}%)")

# Most changed books
top_changed = await tracker.get_most_changed_books(limit=10)
for book in top_changed:
    print(f"{book['title']}: {book['change_count']} changes")
```

### Alerting Rules

Configure custom alerts in `config.py`:

```python
ALERT_RULES = {
    'high_error_rate': {
        'threshold': 0.10,  # 10%
        'window': 3600,     # 1 hour
        'action': 'email'
    },
    'stale_data': {
        'threshold': 48,    # hours
        'action': 'email'
    },
    'database_issues': {
        'threshold': 5,     # consecutive failures
        'action': 'email_urgent'
    }
}
```

## Best Practices

1. **Schedule Optimization**
   - Run full scans during low-traffic periods
   - Space out resource-intensive jobs
   - Consider target website's load

2. **Email Management**
   - Batch notifications when possible
   - Set appropriate thresholds
   - Use rate limiting

3. **Database Maintenance**
   - Regular cleanup of old records
   - Monitor collection sizes
   - Optimize indexes periodically

4. **Error Handling**
   - Review error logs regularly
   - Adjust retry logic based on failure patterns
   - Set up monitoring alerts

5. **Performance**
   - Use concurrent operations where possible
   - Implement connection pooling
   - Monitor resource usage

## Troubleshooting

### Common Issues

**Issue: Jobs not executing**
```bash
# Check scheduler status
python -c "from scheduler.scheduler import BookScheduler; scheduler = BookScheduler(); scheduler.print_jobs()"

# Check APScheduler logs
tail -f logs/scheduler.log
```

**Issue: High memory usage**
```bash
# Reduce batch sizes in config.py
BATCH_SIZE = 50  # Default: 100

# Increase maintenance frequency
MAINTENANCE_SCHEDULE = {'hour': '*/12'}  # Run twice daily
```

**Issue: Email delivery failures**
```bash
# Test email configuration
python -c "from scheduler.notifications import NotificationManager; nm = NotificationManager(); nm.test_connection()"

# Check SMTP credentials
echo $EMAIL_USERNAME
echo $EMAIL_HOST
```

**Issue: Missing changes**
```bash
# Lower significance thresholds
SIGNIFICANT_PRICE_CHANGE_PERCENT = 5  # Default: 10
SIGNIFICANT_CONTENT_CHANGE_PERCENT = 10  # Default: 20
```

## Support and Maintenance

- **Logs Location**: `logs/scheduler.log`
- **Database**: MongoDB collection `scheduler_runs`
- **Health Checks**: Every 15 minutes
- **Automatic Maintenance**: Daily at 3:00 AM

For additional help, review the source code comments or check the main project README.
