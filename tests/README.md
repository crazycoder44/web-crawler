# Web Crawler Test Suite Documentation

## Table of Contents
1. [Overview](#overview)
2. [Test Files](#test-files)
3. [Test Categories](#test-categories)
4. [Setup Instructions](#setup-instructions)
5. [Running Tests](#running-tests)
6. [Expected Results](#expected-results)
7. [Troubleshooting](#troubleshooting)

## Overview

This directory contains a comprehensive test suite for the web crawler and scheduler system. Tests are organized into unit tests, integration tests, and manual verification scripts to ensure all components function correctly both in isolation and as a complete system.

### Test Structure
```
tests/
├── mock_mongo.py              # MongoDB mocking utilities
├── test_connection.py         # Database connection verification
├── test_settings.py           # Configuration testing
├── test_crawler.py            # Crawler functionality tests
├── test_change_detection.py   # Change detection unit tests
├── test_reporting.py          # Report generation tests
├── test_scheduler.py          # Scheduler unit tests
├── test_integration.py        # End-to-end integration tests
└── test_manual_db.py          # Manual real database tests
```

### Test Types
- **Unit Tests**: Test individual components in isolation (mocked dependencies)
- **Integration Tests**: Test component interactions (mocked database)
- **Manual Tests**: Test with real database for verification
- **System Tests**: Full end-to-end workflow validation

## Test Files

### 1. mock_mongo.py
**Type**: Utility Module  
**Purpose**: Provides MongoDB mocking functionality for unit tests

**Key Components:**

#### `MockAsyncIOMotorCursor`
Simulates MongoDB cursor behavior for testing.

**Features:**
- Iterator protocol support
- `to_list()` method
- `sort()` method
- Async iteration support

**Usage Example:**
```python
cursor = MockAsyncIOMotorCursor([{'title': 'Book 1'}, {'title': 'Book 2'}])
results = await cursor.to_list(length=10)
```

#### `MockAsyncIOMotorCollection`
Simulates MongoDB collection operations.

**Supported Operations:**
- `find()`: Query documents
- `find_one()`: Find single document
- `insert_one()`: Insert document
- `insert_many()`: Insert multiple documents
- `update_one()`: Update single document
- `delete_one()`: Delete document
- `count_documents()`: Count matching documents
- `aggregate()`: Aggregation pipeline

**Usage Example:**
```python
collection = MockAsyncIOMotorCollection()
await collection.insert_one({'title': 'Test Book'})
result = await collection.find_one({'title': 'Test Book'})
```

#### `MockAsyncIOMotorDatabase`
Simulates MongoDB database with collections.

**Features:**
- Dynamic collection creation
- Collection access via attribute notation
- Database-level operations

**Usage Example:**
```python
db = MockAsyncIOMotorDatabase()
await db.books.insert_one({'title': 'Book'})
```

**Database Type**: Mock (No real database)  
**Execution**: Used by other test files (not run directly)

---

### 2. test_connection.py
**Type**: Automated (pytest)  
**Purpose**: Verify MongoDB connection and settings configuration

**Database Type**: Real MongoDB Instance  
**Execution Mode**: Automated with pytest

**Test Functions:**

#### `test_connection()`
Tests MongoDB connectivity and basic operations.

**What It Tests:**
1. Settings loading from `.env` file
2. MongoDB connection establishment
3. Database access permissions
4. Collection creation capability
5. Collection cleanup

**How It Works:**
```python
1. Load settings from environment
2. Create MongoDB client
3. Ping MongoDB server
4. Create test collection
5. Drop test collection
6. Assert success
```

**Expected Results:**
```
✓ Successfully connected to MongoDB
✓ Successfully created test collection
✓ Successfully cleaned up test collection
PASSED
```

**How to Run:**
```bash
# Run connection test
python -m pytest tests/test_connection.py -v

# With detailed output
python -m pytest tests/test_connection.py -v -s
```

**Prerequisites:**
- MongoDB server running
- Valid `.env` configuration
- Network connectivity to MongoDB

**Common Issues:**
- Connection refused: MongoDB not running
- Authentication failed: Check credentials
- Database access denied: Check permissions

---

### 3. test_settings.py
**Type**: Automated (pytest)  
**Purpose**: Validate configuration management and settings

**Database Type**: No database  
**Execution Mode**: Automated with pytest

**Test Functions:**

#### `test_settings_load()`
Verifies settings are loaded correctly.

**What It Tests:**
- Environment variable parsing
- Default values
- Required settings presence
- Type validation

**Expected Results:**
```python
{
    'mongo_uri': 'mongodb://localhost:27017',
    'database_name': 'books_crawler',
    'base_url': 'https://books.toscrape.com',
    'checkpoint_interval': 10
}
```

#### `test_settings_validation()`
Tests settings validation logic.

**What It Tests:**
- Invalid MongoDB URI handling
- Missing required settings
- Type mismatches
- Value constraints

**Expected Results:**
```
✓ Invalid URI raises ValueError
✓ Missing required field raises ValidationError
✓ Type mismatch handled correctly
PASSED (3/3 tests)
```

**How to Run:**
```bash
python -m pytest tests/test_settings.py -v
```

**Prerequisites:**
- `.env` file present
- Valid configuration format

---

### 4. test_crawler.py
**Type**: Manual Script  
**Purpose**: Full crawler functionality verification with real website

**Database Type**: Real MongoDB Instance  
**Execution Mode**: Manual execution (not pytest)

**What It Tests:**
1. Complete book crawling workflow
2. Category navigation
3. Pagination handling
4. Data extraction accuracy
5. Database storage
6. Checkpoint management
7. Error handling

**How It Works:**
```python
async def main():
    # 1. Initialize crawler
    crawler = BooksCrawler(checkpoint_interval=20)
    
    # 2. Run full crawl
    stats = await crawler.run()
    
    # 3. Validate results
    books = await db.books.find().to_list(length=None)
    
    # 4. Generate report
    print_crawl_statistics(books, stats)
```

**Expected Results:**
```
=== Crawl Results ===
Total books crawled: 1000
Categories found: 50
Error count: 0
Books with descriptions: 998
Price range: £10.00 - £59.99 (avg: £35.07)

Rating distribution:
  1 stars: 226 books
  2 stars: 196 books
  3 stars: 203 books
  4 stars: 179 books
  5 stars: 196 books

✓ Successfully crawled all books

Sample successful book:
  Title: The Road to Little Dribbling...
  Category: Travel
  Price: £23.21
  Rating: 1 stars

Duration: 0:04:24
```

**How to Run:**
```bash
# Direct execution
python -m tests.test_crawler

# With output logging
python -m tests.test_crawler > crawler_test.log 2>&1
```

**Prerequisites:**
- MongoDB running
- Internet connectivity
- Target website accessible (books.toscrape.com)
- Sufficient disk space (~50MB)

**Performance Metrics:**
- Duration: ~4-5 minutes for 1000 books
- Network requests: ~1100 (books + categories)
- Database writes: ~1000 documents
- Memory usage: ~150-200MB peak

**What to Check:**
- ✓ All 1000 books crawled
- ✓ All 50 categories processed
- ✓ No failed URLs
- ✓ Descriptions present (99%+)
- ✓ Valid price ranges
- ✓ Rating distribution reasonable
- ✓ Checkpoints saved correctly

---

### 5. test_change_detection.py
**Type**: Automated (pytest)  
**Purpose**: Unit tests for change detection functionality

**Database Type**: Mock (no real database)  
**Execution Mode**: Automated with pytest

**Test Functions:**

#### `test_detect_price_change()`
Tests price change detection.

**Scenario:**
```python
old_book = Book(title='Test', price=29.99)
new_book = Book(title='Test', price=24.99)
```

**Expected Result:**
```python
{
    'change_type': 'price',
    'old_value': 29.99,
    'new_value': 24.99,
    'change_percentage': -16.67,
    'significant': True  # >10% change
}
```

#### `test_detect_availability_change()`
Tests stock status change detection.

**Scenarios:**
- In Stock → Out of Stock
- Out of Stock → In Stock

**Expected Result:**
```python
{
    'change_type': 'availability',
    'old_value': 'in_stock',
    'new_value': 'out_of_stock',
    'significant': True
}
```

#### `test_detect_content_change()`
Tests description change detection.

**What It Tests:**
- Text similarity calculation
- Significance threshold (20%)
- Fingerprint comparison

**Expected Result:**
```python
{
    'change_type': 'content',
    'similarity': 0.15,  # 85% different
    'significant': True
}
```

#### `test_no_significant_changes()`
Tests filtering of insignificant changes.

**Scenarios:**
- Price change <10% and <$5
- Description change <20%

**Expected Result:**
```python
change = None  # No change recorded
```

#### `test_consolidate_changes()`
Tests change aggregation.

**What It Tests:**
- Multiple changes for same book
- Change deduplication
- Change prioritization

**Expected Result:**
```python
{
    'price_changes': 5,
    'availability_changes': 3,
    'content_changes': 2,
    'total_unique_books': 8
}
```

**How to Run:**
```bash
# Run all change detection tests
python -m pytest tests/test_change_detection.py -v

# Run specific test
python -m pytest tests/test_change_detection.py::test_detect_price_change -v

# With coverage
python -m pytest tests/test_change_detection.py --cov=scheduler.change_tracker
```

**Expected Results:**
```
tests/test_change_detection.py::test_detect_price_change PASSED
tests/test_change_detection.py::test_detect_availability_change PASSED
tests/test_change_detection.py::test_detect_content_change PASSED
tests/test_change_detection.py::test_no_significant_changes PASSED
tests/test_change_detection.py::test_consolidate_changes PASSED

========== 5 passed in 0.23s ==========
```

---

### 6. test_reporting.py
**Type**: Automated (pytest)  
**Purpose**: Unit tests for report generation system

**Database Type**: Mock (no real database)  
**Execution Mode**: Automated with pytest

**Test Functions:**

#### `test_record_change()`
Tests recording individual changes.

**What It Tests:**
```python
change = {
    'book_id': '507f...',
    'change_type': 'price',
    'old_value': 19.99,
    'new_value': 24.99
}
await reporter.record_change(change)
```

**Expected Result:**
- Change stored in database
- Returns change ID
- Timestamp added automatically

#### `test_generate_daily_report()`
Tests daily report generation.

**What It Tests:**
- Change aggregation
- Statistics calculation
- Report formatting

**Expected Result:**
```python
{
    'date': '2025-11-09',
    'total_changes': 45,
    'price_changes': 20,
    'availability_changes': 15,
    'content_changes': 10,
    'top_price_increases': [...],
    'top_price_decreases': [...],
    'statistics': {...}
}
```

#### `test_export_report_json()`
Tests JSON report export.

**What It Tests:**
- JSON serialization
- File writing
- Data integrity

**Expected Result:**
- File created: `reports/daily_report_2025-11-09.json`
- Valid JSON format
- All data preserved

#### `test_export_report_csv()`
Tests CSV report export.

**What It Tests:**
- CSV formatting
- Header row
- Data conversion

**Expected Result:**
- File created: `reports/daily_report_2025-11-09.csv`
- Valid CSV format
- Proper escaping

#### `test_weekly_trends()`
Tests weekly trend analysis.

**What It Tests:**
- Time-series aggregation
- Trend calculation
- Statistical analysis

**Expected Result:**
```python
{
    'week_start': '2025-11-03',
    'week_end': '2025-11-09',
    'total_changes': 315,
    'daily_average': 45,
    'trends': {
        'price': 'increasing',
        'availability': 'stable'
    }
}
```

**How to Run:**
```bash
# Run all reporting tests
python -m pytest tests/test_reporting.py -v

# Test specific functionality
python -m pytest tests/test_reporting.py::test_generate_daily_report -v

# With output capture disabled
python -m pytest tests/test_reporting.py -v -s
```

**Expected Results:**
```
tests/test_reporting.py::test_record_change PASSED
tests/test_reporting.py::test_generate_daily_report PASSED
tests/test_reporting.py::test_export_report_json PASSED
tests/test_reporting.py::test_export_report_csv PASSED
tests/test_reporting.py::test_weekly_trends PASSED

========== 5 passed in 0.31s ==========
```

---

### 7. test_scheduler.py
**Type**: Automated (pytest)  
**Purpose**: Unit tests for scheduler functionality

**Database Type**: Mock (no real database)  
**Execution Mode**: Automated with pytest

**Test Functions:**

#### `test_scheduler_initialization()`
Tests scheduler setup.

**What It Tests:**
- Scheduler creation
- Job configuration
- Trigger setup
- Event listeners

**Expected Result:**
```python
jobs = ['full_site_scan', 'change_detection', 'maintenance', 'health_check']
assert all(job in scheduler.get_jobs() for job in jobs)
```

#### `test_scheduler_job_error_handling()`
Tests error recovery.

**What It Tests:**
- Exception catching
- Error logging
- Retry mechanism
- Notification sending

**Simulated Scenario:**
```python
# Job fails 2 times, succeeds on 3rd attempt
attempt_results = ['error', 'error', 'success']
```

**Expected Result:**
- Errors logged
- Retries executed
- Final success recorded
- No data loss

#### `test_full_site_scan_job()`
Tests full scan job execution.

**What It Tests:**
- Crawler initialization
- Job execution
- Result recording
- Statistics generation

**Mocked Behavior:**
```python
crawler_stats = {
    'total_books': 1000,
    'categories_processed': 50,
    'failed_urls': 0
}
```

**Expected Result:**
- Job completes successfully
- Stats match expected values
- Database updated

#### `test_change_detection_job()`
Tests change detection job.

**What It Tests:**
- Recent book querying
- Change comparison
- Notification triggering
- Result aggregation

**Expected Result:**
```python
{
    'total_checked': 100,
    'changes_detected': 15,
    'notifications_sent': 5
}
```

#### `test_maintenance_job()`
Tests maintenance operations.

**What It Tests:**
- Old record cleanup
- Index optimization
- Checkpoint cleanup
- Report generation

**Expected Result:**
```python
{
    'records_deleted': 1500,
    'space_freed_mb': 25,
    'indexes_optimized': 3
}
```

#### `test_health_check_job()`
Tests health monitoring.

**What It Tests:**
- Database connectivity
- Website availability
- Job status
- Error rates

**Expected Result:**
```python
{
    'database_status': 'healthy',
    'website_status': 'healthy',
    'last_scan_age_hours': 2,
    'error_rate': 0.02
}
```

**How to Run:**
```bash
# Run all scheduler tests
python -m pytest tests/test_scheduler.py -v

# Test specific job
python -m pytest tests/test_scheduler.py::test_full_site_scan_job -v

# With coverage report
python -m pytest tests/test_scheduler.py --cov=scheduler
```

**Expected Results:**
```
tests/test_scheduler.py::test_scheduler_initialization PASSED
tests/test_scheduler.py::test_scheduler_job_error_handling PASSED
tests/test_scheduler.py::test_full_site_scan_job PASSED
tests/test_scheduler.py::test_change_detection_job PASSED
tests/test_scheduler.py::test_maintenance_job PASSED
tests/test_scheduler.py::test_health_check_job PASSED

========== 6 passed in 0.42s ==========
```

---

### 8. test_integration.py
**Type**: Automated (pytest)  
**Purpose**: End-to-end integration testing

**Database Type**: Mock (no real database)  
**Execution Mode**: Automated with pytest

**Test Functions:**

#### `test_complete_workflow()`
Tests full system workflow.

**Workflow Steps:**
1. Initialize scheduler
2. Run full site scan
3. Detect changes
4. Generate reports
5. Send notifications
6. Run maintenance

**What It Tests:**
- Component integration
- Data flow between components
- Error propagation
- State consistency

**Expected Result:**
```
✓ Scheduler initialized
✓ Full scan completed (1000 books)
✓ Changes detected (15 changes)
✓ Reports generated (daily + weekly)
✓ Notifications sent (5 emails)
✓ Maintenance completed
WORKFLOW PASSED
```

#### `test_crawler_to_database_integration()`
Tests crawler-database interaction.

**What It Tests:**
- Book data storage
- Index creation
- Query performance
- Data integrity

**Expected Result:**
- All books stored correctly
- Indexes created
- Queries execute in <100ms
- No data corruption

#### `test_change_detection_integration()`
Tests change detection workflow.

**What It Tests:**
- Book querying
- Change comparison
- Change recording
- Notification triggering

**Expected Result:**
- Changes detected correctly
- All significant changes recorded
- Notifications sent appropriately
- Database updated

#### `test_notification_integration()`
Tests notification system.

**What It Tests:**
- Email composition
- Template rendering
- SMTP connection
- Delivery confirmation

**Mocked Behavior:**
- SMTP server responses
- Email delivery status

**Expected Result:**
- Emails composed correctly
- Templates rendered with data
- No connection errors
- All emails "sent"

#### `test_error_recovery_integration()`
Tests system recovery from failures.

**Failure Scenarios:**
- Database disconnection
- Network timeout
- Invalid data
- Resource exhaustion

**Expected Result:**
- Errors caught and logged
- Retries executed
- Partial results saved
- System remains stable

**How to Run:**
```bash
# Run all integration tests
python -m pytest tests/test_integration.py -v

# Run specific test
python -m pytest tests/test_integration.py::test_complete_workflow -v

# With detailed logging
python -m pytest tests/test_integration.py -v -s --log-cli-level=INFO
```

**Expected Results:**
```
tests/test_integration.py::test_complete_workflow PASSED
tests/test_integration.py::test_crawler_to_database_integration PASSED
tests/test_integration.py::test_change_detection_integration PASSED
tests/test_integration.py::test_notification_integration PASSED
tests/test_integration.py::test_error_recovery_integration PASSED

========== 5 passed in 2.15s ==========
```

**Performance Expectations:**
- Complete workflow: <3 seconds (mocked)
- Database operations: <500ms per test
- Memory usage: <100MB

---

### 9. test_manual_db.py
**Type**: Manual Script  
**Purpose**: Real database verification and reporting validation

**Database Type**: Real MongoDB Instance  
**Execution Mode**: Manual execution (not pytest)

**What It Tests:**
1. Real database connectivity
2. Report generation with actual data
3. Change tracking functionality
4. Notification system with real templates
5. Data aggregation accuracy

**How It Works:**
```python
async def test_real_database():
    # 1. Connect to test database
    client = AsyncIOMotorClient(uri)
    db = client['manual_test_bookstore']
    
    # 2. Insert test data
    await db.books.insert_many(test_books)
    
    # 3. Insert test changes
    await db.book_changes.insert_many(test_changes)
    
    # 4. Generate reports
    daily_report = await reporter.generate_daily_report()
    
    # 5. Test notifications
    await notifications.send_change_alert(change)
    
    # 6. Cleanup
    await db.drop_database()
```

**Test Data:**
- 5 sample books with realistic data
- 10 change records (price, availability, content)
- Multiple change types and severities

**What It Validates:**

1. **Database Operations**
   ```
   ✓ Connected to MongoDB
   ✓ Test database created
   ✓ Books inserted (5 books)
   ✓ Changes inserted (10 changes)
   ```

2. **Report Generation**
   ```
   ✓ Daily report generated
   ✓ Change aggregation correct
   ✓ Statistics calculated
   ✓ Reports saved to files
   ```

3. **Query Performance**
   ```
   ✓ Book queries < 50ms
   ✓ Change queries < 100ms
   ✓ Aggregations < 200ms
   ```

4. **Data Integrity**
   ```
   ✓ All books retrievable
   ✓ Changes linked to books
   ✓ No orphaned records
   ```

**Expected Console Output:**
```
============================================================
MANUAL DATABASE TEST
============================================================

✓ Connected to MongoDB: mongodb://localhost:27017
✓ Using test database: manual_test_bookstore

------------------------------------------------------------
STEP 1: Inserting test books
------------------------------------------------------------
✓ Inserted 5 test books

------------------------------------------------------------
STEP 2: Inserting test changes
------------------------------------------------------------
✓ Inserted 10 test changes
  - Price changes: 5
  - Availability changes: 3
  - Content changes: 2

------------------------------------------------------------
STEP 3: Generating daily report
------------------------------------------------------------
✓ Daily report generated
  Total changes: 10
  Significant changes: 7
  Report saved to: reports/daily_report_manual_test.json

------------------------------------------------------------
STEP 4: Testing notifications
------------------------------------------------------------
✓ Price change notification composed
✓ Availability change notification composed
✓ Content change notification composed

------------------------------------------------------------
STEP 5: Testing report queries
------------------------------------------------------------
✓ Query execution time: 45ms
✓ All changes retrieved correctly
✓ Statistics match expected values

------------------------------------------------------------
STEP 6: Cleanup
------------------------------------------------------------
✓ Test database dropped
✓ Temporary files removed

============================================================
TEST COMPLETED SUCCESSFULLY
============================================================
```

**How to Run:**
```bash
# Direct execution
python -m tests.test_manual_db

# With output capture
python tests/test_manual_db.py > manual_test_results.log 2>&1

# With verbose logging
LOG_LEVEL=DEBUG python -m tests.test_manual_db
```

**Prerequisites:**
- MongoDB server running
- Valid `.env` configuration
- Write permissions for `reports/` directory
- Internet connectivity (for potential external dependencies)

**Files Created:**
- `reports/daily_report_manual_test.json`
- `reports/change_summary_manual_test.csv`
- `logs/manual_test.log` (if logging enabled)

**Cleanup:**
- Automatically drops test database
- Removes temporary files
- Closes all connections

**Common Issues:**
- Database already exists: Script will overwrite
- Permission denied: Check MongoDB user permissions
- Connection timeout: Increase timeout in settings

---

## Test Categories

### Unit Tests (Mocked Database)
**Files:**
- `test_settings.py`
- `test_change_detection.py`
- `test_reporting.py`
- `test_scheduler.py`

**Characteristics:**
- Fast execution (<1 second per test)
- No external dependencies
- Uses mock objects
- Isolated component testing
- Deterministic results

**Run Command:**
```bash
python -m pytest tests/test_settings.py tests/test_change_detection.py tests/test_reporting.py tests/test_scheduler.py -v
```

### Integration Tests (Mocked Database)
**Files:**
- `test_integration.py`

**Characteristics:**
- Tests component interactions
- Uses mocked database
- Longer execution time (1-3 seconds per test)
- End-to-end workflow validation

**Run Command:**
```bash
python -m pytest tests/test_integration.py -v
```

### Real Database Tests
**Files:**
- `test_connection.py` (automated with pytest)
- `test_manual_db.py` (manual execution)
- `test_crawler.py` (manual execution)

**Characteristics:**
- Requires MongoDB running
- Real network requests
- Longer execution time
- Cleanup required
- More comprehensive validation

**Run Commands:**
```bash
# Automated
python -m pytest tests/test_connection.py -v

# Manual
python -m tests.test_manual_db
python -m tests.test_crawler
```

---

## Setup Instructions

### 1. Environment Setup

Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB
# Windows: Download from mongodb.com
# Linux: sudo apt-get install mongodb
# macOS: brew install mongodb-community

# Start MongoDB
mongod --dbpath /path/to/data
```

**Option B: MongoDB Atlas**
```
1. Create account at mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string
4. Add to .env file
```

### 3. Configuration

Create `.env` file:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=books_crawler

# Test Settings
TEST_DATABASE=test_books_crawler
LOG_LEVEL=INFO

# Email Configuration (for notification tests)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=Test Crawler <test@crawler.com>
EMAIL_TO=test@example.com
```

### 4. Directory Structure

Create required directories:
```bash
mkdir -p logs
mkdir -p reports
mkdir -p temp
```

---

## Running Tests

### Run All Tests
```bash
# All automated tests (pytest)
python -m pytest tests/ -v

# Exclude manual tests
python -m pytest tests/ -v --ignore=tests/test_manual_db.py --ignore=tests/test_crawler.py
```

### Run Test Categories

**Unit Tests Only:**
```bash
python -m pytest tests/test_settings.py tests/test_change_detection.py tests/test_reporting.py tests/test_scheduler.py -v
```

**Integration Tests:**
```bash
python -m pytest tests/test_integration.py -v
```

**Connection Tests:**
```bash
python -m pytest tests/test_connection.py -v
```

**Manual Tests:**
```bash
# Database verification
python -m tests.test_manual_db

# Crawler verification
python -m tests.test_crawler
```

### Run with Coverage

**Generate coverage report:**
```bash
# All tests
python -m pytest tests/ --cov=scheduler --cov=crawler --cov-report=html

# Specific module
python -m pytest tests/test_scheduler.py --cov=scheduler.scheduler --cov-report=term-missing
```

**View coverage:**
```bash
# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run with Logging

**Enable detailed logging:**
```bash
python -m pytest tests/ -v -s --log-cli-level=INFO

# Debug level
python -m pytest tests/ -v -s --log-cli-level=DEBUG

# Save to file
python -m pytest tests/ -v --log-file=test_output.log
```

### Run Specific Tests

**Single test file:**
```bash
python -m pytest tests/test_scheduler.py -v
```

**Single test function:**
```bash
python -m pytest tests/test_scheduler.py::test_full_site_scan_job -v
```

**Tests matching pattern:**
```bash
python -m pytest tests/ -k "change_detection" -v
python -m pytest tests/ -k "not integration" -v
```

---

## Expected Results

### Successful Test Run

**Unit Tests:**
```
tests/test_settings.py::test_settings_load PASSED                    [ 10%]
tests/test_settings.py::test_settings_validation PASSED              [ 20%]
tests/test_change_detection.py::test_detect_price_change PASSED     [ 30%]
tests/test_change_detection.py::test_detect_availability_change PASSED [ 40%]
tests/test_change_detection.py::test_consolidate_changes PASSED     [ 50%]
tests/test_reporting.py::test_record_change PASSED                   [ 60%]
tests/test_reporting.py::test_generate_daily_report PASSED           [ 70%]
tests/test_scheduler.py::test_scheduler_initialization PASSED        [ 80%]
tests/test_scheduler.py::test_full_site_scan_job PASSED              [ 90%]
tests/test_scheduler.py::test_maintenance_job PASSED                 [100%]

========== 10 passed in 1.23s ==========
```

**Integration Tests:**
```
tests/test_integration.py::test_complete_workflow PASSED             [ 20%]
tests/test_integration.py::test_crawler_to_database_integration PASSED [ 40%]
tests/test_integration.py::test_change_detection_integration PASSED  [ 60%]
tests/test_integration.py::test_notification_integration PASSED      [ 80%]
tests/test_integration.py::test_error_recovery_integration PASSED    [100%]

========== 5 passed in 2.15s ==========
```

**Connection Test:**
```
tests/test_connection.py::test_connection PASSED                     [100%]
✓ Successfully connected to MongoDB
✓ Successfully created test collection
✓ Successfully cleaned up test collection

========== 1 passed in 0.52s ==========
```

### Performance Benchmarks

**Unit Tests:**
- Individual test: <0.1 seconds
- Full suite: <2 seconds
- Memory: <50MB

**Integration Tests:**
- Individual test: 0.2-0.5 seconds
- Full suite: <3 seconds
- Memory: <100MB

**Manual Tests:**
- test_manual_db.py: 2-5 seconds
- test_crawler.py: 4-6 minutes
- Memory: 150-200MB

### Coverage Expectations

**Target Coverage:**
- Overall: >85%
- Core modules: >90%
- Utilities: >80%

**Coverage Report Example:**
```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
scheduler/__init__.py                 3      0   100%
scheduler/scheduler.py               85      7    92%   45-47, 112-115
scheduler/jobs.py                   156     12    92%   78-82, 195-198
scheduler/change_tracker.py          98      8    92%   67-70, 134-138
scheduler/reporting.py              124     15    88%   89-95, 156-162
scheduler/notifications.py           76     18    76%   45-52, 98-107
---------------------------------------------------------------
TOTAL                               542     60    89%
```

---

## Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed
```
Error: ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused
```

**Solutions:**
- Start MongoDB: `mongod --dbpath /data/db`
- Check connection string in `.env`
- Verify MongoDB is running: `mongo --eval "db.version()"`
- Check firewall settings

#### 2. Import Errors
```
Error: ModuleNotFoundError: No module named 'scheduler'
```

**Solutions:**
- Install dependencies: `pip install -r requirements.txt`
- Check Python path: `echo $PYTHONPATH`
- Run from project root directory
- Activate virtual environment

#### 3. Test Failures
```
FAILED tests/test_integration.py::test_complete_workflow
```

**Debugging Steps:**
```bash
# Run with verbose output
python -m pytest tests/test_integration.py::test_complete_workflow -vv

# Run with logging
python -m pytest tests/test_integration.py::test_complete_workflow -v -s --log-cli-level=DEBUG

# Run with debugger
python -m pytest tests/test_integration.py::test_complete_workflow --pdb
```

#### 4. Slow Test Execution
```
Tests taking longer than expected
```

**Solutions:**
- Use mock database for unit tests
- Reduce data size in manual tests
- Run tests in parallel: `pytest -n auto`
- Check network connectivity
- Verify MongoDB performance

#### 5. Permission Errors
```
Error: PermissionError: [Errno 13] Permission denied: 'reports/daily_report.json'
```

**Solutions:**
```bash
# Create directories
mkdir -p logs reports temp

# Set permissions
chmod 755 logs reports temp

# Check disk space
df -h
```

#### 6. Email Notification Failures
```
Error: SMTPAuthenticationError: Username and Password not accepted
```

**Solutions:**
- Use app-specific password (Gmail)
- Enable less secure apps (not recommended)
- Check SMTP credentials in `.env`
- Verify email server settings
- Test with mock notifications in unit tests

### Debug Mode

Enable comprehensive debugging:

```bash
# Set environment variables
export DEBUG=1
export LOG_LEVEL=DEBUG

# Run tests with full output
python -m pytest tests/ -vv -s --log-cli-level=DEBUG --tb=long

# Save debug output
python -m pytest tests/ -vv -s --log-cli-level=DEBUG > debug_output.log 2>&1
```

### Clean Test Environment

Reset test environment:

```bash
# Remove temporary files
rm -rf temp/ logs/ reports/

# Drop test databases
mongo test_books_crawler --eval "db.dropDatabase()"

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Recreate directories
mkdir -p logs reports temp
```

### Performance Profiling

Profile test execution:

```bash
# Install profiler
pip install pytest-profiling

# Run with profiling
python -m pytest tests/ --profile

# Generate profile report
python -m pytest tests/ --profile-svg

# View results
open prof/combined.svg
```

---

## Test Maintenance

### Adding New Tests

1. **Create test file** in `tests/` directory
2. **Import required modules**
   ```python
   import pytest
   import pytest_asyncio
   from unittest.mock import Mock, AsyncMock
   ```
3. **Define fixtures** for setup/teardown
4. **Write test functions** with descriptive names
5. **Add to appropriate category** (unit/integration/manual)
6. **Update this README** with test documentation

### Test Best Practices

1. **Naming Convention:**
   - Test files: `test_<module>.py`
   - Test functions: `test_<functionality>()`
   - Fixtures: `<resource_name>()`

2. **Documentation:**
   - Docstrings for complex tests
   - Comments for non-obvious logic
   - README entry for manual tests

3. **Assertions:**
   - Use descriptive assertion messages
   - Test expected behavior, not implementation
   - One logical assertion per test

4. **Fixtures:**
   - Reuse fixtures across tests
   - Clean up resources in teardown
   - Use appropriate scope (function/module/session)

5. **Mocking:**
   - Mock external dependencies
   - Use `AsyncMock` for async functions
   - Verify mock calls when relevant

---

## Additional Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Motor (async MongoDB)**: https://motor.readthedocs.io/
- **AsyncIO Testing**: https://docs.python.org/3/library/asyncio-dev.html
- **Coverage.py**: https://coverage.readthedocs.io/

For project-specific questions, refer to:
- Main project README
- Scheduler documentation (`scheduler/README.md`)
- Source code comments
