# Books Crawler# Books Crawler



A robust, asynchronous web crawler designed to extract book information from [Books to Scrape](https://books.toscrape.com/), implementing intelligent pagination handling, category-based crawling, change detection, and MongoDB storage with GridFS support.A robust, asynchronous web crawler designed to extract book information from [Books to Scrape](https://books.toscrape.com/), implementing pagination handling and category-based crawling with MongoDB storage.



## Table of Contents## Features

1. [Features](#features)

2. [Architecture](#architecture)- ✨ Asynchronous crawling with concurrency control

3. [Components](#components)- 📚 Category-based book extraction

4. [Prerequisites](#prerequisites)- 💾 MongoDB storage with deduplication

5. [Configuration](#configuration)- 🔄 Checkpoint system for resumable crawls

6. [Data Model](#data-model)- 📊 Detailed logging and statistics

7. [Installation](#installation)- ⚡ Rate limiting and request throttling

8. [Usage](#usage)- 🛡️ Error handling and retry mechanisms

9. [Crawler Behavior](#crawler-behavior)

10. [Testing](#testing)## Architecture

11. [Performance](#performance)

12. [Error Handling](#error-handling)The crawler is composed of several key components:

13. [Advanced Features](#advanced-features)

14. [Troubleshooting](#troubleshooting)- `client.py`: Handles HTTP requests with rate limiting and retries

- `models.py`: Defines data models for books and other entities

## Features- `parsers.py`: Contains HTML parsing logic for extracting book information

- `runner.py`: Implements the main crawler execution logic

- ✨ **Asynchronous Crawling**: Non-blocking I/O with configurable concurrency control- `settings.py`: Manages configuration and environment variables

- 📚 **Category-Based Extraction**: Systematically crawls all 50 book categories- `store.py`: Handles MongoDB database operations

- 💾 **MongoDB Storage**: Persistent storage with automatic deduplication using content fingerprinting

- 🔄 **Checkpoint System**: Resume crawls from last successful state after interruptions## Prerequisites

- 📊 **Detailed Statistics**: Real-time logging with comprehensive crawl metrics

- ⚡ **Rate Limiting**: Configurable request throttling to respect server resources- Python 3.10 or higher

- 🛡️ **Retry Mechanisms**: Exponential backoff retry logic for transient failures- MongoDB 4.4 or higher

- 🔍 **Change Detection**: Intelligent tracking of price, availability, and content changes- Required Python packages (see requirements.txt)

- 📦 **GridFS Support**: Optional HTML snapshot storage in MongoDB GridFS

- 🎯 **Pagination Handling**: Smart navigation through multi-page categories## Configuration

- 📈 **Progress Tracking**: Real-time progress updates and checkpoint saves

- 🔒 **Thread-Safe Operations**: Semaphore-based concurrency managementThe crawler uses environment variables for configuration. Create a `.env` file with:



## Architecture```env

mongo_uri=mongodb://localhost:27017/books

```max_concurrency=10

crawler/request_timeout=10

├── client.py           # HTTP client with rate limiting and retriesretry_attempts=5

├── models.py          # Pydantic data models and validationuser_agent=BooksCrawler/1.0 (+https://github.com/your-github-username/)

├── parsers.py         # BeautifulSoup-based HTML parsingstore_html_in_gridfs=true

├── runner.py          # Main crawler orchestration and execution```

├── settings.py        # Configuration management with .env support

├── store.py           # MongoDB operations and change tracking## Testing

├── logging_config.py  # Logging configuration

└── __init__.py        # Package initialization### 1. Test Database Connection

```

First, ensure MongoDB is running and test the connection:

### Data Flow

``````bash

1. Runner → Client: Fetch HTMLpython -m tests.test_connection

2. Client → Parser: Extract data```

3. Parser → Models: Validate data

4. Models → Store: Persist to MongoDBExpected output:

5. Store → Change Detection: Compare with previous data```

6. Store → GridFS: Save HTML snapshots (optional)INFO: MongoDB connection successful

```INFO: Database name: books

INFO: Collections: ['books', 'raw_html']

## Components```



### 1. client.py - HTTP Client### 2. Test Crawler



**Purpose**: Manages all HTTP requests with intelligent retry and rate limiting.Run the crawler test which will attempt to crawl all books:



**Key Features:**```bash

- Asynchronous HTTP client using `httpx`python -m tests.test_crawler

- Automatic retry on network errors (5xx status codes)```

- Configurable exponential backoff

- Rate limiting with request interval controlThe test will:

- User-agent customization- Crawl all book categories

- Redirect following- Extract and store book information

- Thread-safe request coordination- Save raw HTML content

- Generate crawl statistics

**Configuration:**

```python## Data Model

request_timeout: int = 10      # Seconds before request times out

retry_attempts: int = 5        # Number of retry attemptsBooks are stored with the following structure:

request_interval: float = 1.0  # Minimum seconds between requests

user_agent: str = "BooksCrawler/1.0"```python

```{

    'title': str,

**Error Handling:**    'source_url': HttpUrl,

- `NetworkError`: Automatic retry with exponential backoff    'description': Optional[str],

- `TimeoutException`: Retry with increased timeout    'category': str,

- `5xx errors`: Retry (server errors)    'price_incl_tax': float,

- `4xx errors`: Log and skip (client errors, no retry)    'price_excl_tax': float,

    'availability': str,

**Rate Limiting Implementation:**    'num_reviews': int,

```python    'image_url': HttpUrl,

# Ensures minimum request_interval between consecutive requests    'rating': int,

async with self._lock:    'fingerprint': str,

    time_since_last = now - self.last_request_time    'crawl_timestamp': datetime,

    if time_since_last < settings.request_interval:    'status': str,

        await asyncio.sleep(settings.request_interval - time_since_last)    'http_status': int

```}

```

### 2. models.py - Data Models

## Crawler Behavior

**Purpose**: Defines validated data structures using Pydantic.

1. **Category Discovery**:

**Primary Model: Book**   - Starts from the main index page

```python   - Extracts all book categories

class Book(BaseModel):   - Processes each category sequentially

    source_url: HttpUrl              # Original book page URL

    title: str                       # Book title2. **Book Processing**:

    description: Optional[str]       # Book description   - Extracts books from category pages

    category: Optional[str]          # Category name   - Handles pagination within categories

    price_incl_tax: Optional[float]  # Price including tax (> 0)   - Processes book detail pages concurrently (controlled by MAX_CONCURRENCY)

    price_excl_tax: Optional[float]  # Price excluding tax (> 0)

    availability: Optional[str]      # Stock status3. **Data Storage**:

    num_reviews: Optional[int]       # Review count (≥ 0)   - Deduplicates books using content fingerprinting

    image_url: Optional[HttpUrl]     # Cover image URL   - Stores raw HTML for future reference

    rating: Optional[int]            # Star rating (0-5)   - Creates checkpoints for resumable operations

    raw_html_hash: str               # SHA-256 hash of HTML

    raw_html_snapshot_path: Optional[str]  # GridFS path4. **Error Handling**:

    crawl_timestamp: datetime        # When crawled   - Retries failed requests

    status: str                      # "ok", "error", or "retry"   - Logs errors for debugging

    response_time: Optional[float]   # Request duration   - Maintains crawl statistics

    http_status: Optional[int]       # HTTP status code (100-599)

    id: Optional[str]                # MongoDB ObjectId## Statistics and Logging

```

The crawler generates detailed statistics including:

**Validation:**- Total books crawled

- URLs validated and normalized- Categories processed

- Prices must be positive- Success/failure counts

- Ratings constrained to 0-5- Duration of crawl

- Review counts non-negative- Price and rating distributions

- HTTP status codes in valid range

Logs are stored with timestamps and contain:

### 3. parsers.py - HTML Parsing- Crawl progress information

- HTTP request details

**Purpose**: Extracts structured data from HTML using BeautifulSoup.- Error messages and stack traces

- Checkpoint creation events

**Key Functions:**

## Performance

#### `extract_categories(html: str) -> List[Tuple[str, str]]`

Extracts all book categories from the main page.Typical performance metrics:

- Crawl speed: ~5 books/second

**Returns:** List of (category_name, category_url) tuples- Average crawl time: 3-4 minutes for 1000 books

- Memory usage: ~100MB

**Example:**- Network efficiency: Respects rate limits

```python

[## Error Recovery

    ("Travel", "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"),

    ("Mystery", "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html")The crawler implements several recovery mechanisms:

]- Automatic retry on failed requests

```- Checkpoint-based resume capability

- Transaction-based MongoDB operations

#### `extract_books_from_list(html: str) -> List[Tuple[str, str]]`- Connection pool management

Extracts book URLs from category listing pages.

## Future Improvements

**Handles:**

- Relative URL resolution- [ ] Add support for proxy rotation

- Path normalization (removes `../`, adds `/catalogue/`)- [ ] Implement adaptive rate limiting

- Title extraction- [ ] Add support for distributed crawling

- [ ] Enhance data validation and cleaning

**Returns:** List of (title, url) tuples- [ ] Add support for incremental updates

#### `get_next_page_url(html: str, current_url: str) -> Optional[str]`
Intelligently determines the next pagination page.

**Algorithm:**
```python
1. Find <li class="next"><a> element
2. Extract relative href
3. Resolve relative to current page directory
4. Return absolute URL or None
```

**Handles:**
- Category pagination (page-2.html, page-3.html, etc.)
- Main index pagination
- End-of-pagination detection

#### `extract_book_data(html: str, url: str) -> Dict[str, Any]`
Comprehensive extraction of all book data from detail pages.

**Extracts:**
- Title (from `<h1>`)
- Description (from `#product_description + p`)
- Price including tax (from product information table)
- Price excluding tax (from product information table)
- Availability (from stock status)
- Number of reviews (parsed from text)
- Rating (from CSS class: One→1, Two→2, etc.)
- Image URL (from `#product_gallery img`)

**Data Cleaning:**
- Removes extra whitespace
- Normalizes currency symbols
- Parses numeric values from text
- Handles missing elements gracefully

### 4. runner.py - Crawler Orchestration

**Purpose**: Main execution logic coordinating all crawler components.

**Class: BooksCrawler**

**Initialization:**
```python
BooksCrawler(
    start_url: str = "https://books.toscrape.com/",
    checkpoint_interval: int = 10  # Save checkpoint every N books
)
```

**Key Methods:**

#### `async def run() -> Dict[str, Any]`
Executes the complete crawl workflow.

**Steps:**
1. Initialize MongoDB indexes
2. Fetch and parse main index page
3. Extract all categories
4. For each category:
   - Fetch category page
   - Extract book URLs
   - Handle pagination
   - Crawl book detail pages (concurrent)
5. Save checkpoints periodically
6. Generate statistics

**Returns:**
```python
{
    'total_books': 1000,
    'categories_processed': 50,
    'failed_urls': 0,
    'duration_seconds': 264.31,
    'successful': True
}
```

#### `async def crawl_book_page(url: str, category: str) -> Optional[str]`
Crawls a single book detail page.

**Process:**
1. Check if URL already seen (deduplication)
2. Acquire semaphore slot (concurrency control)
3. Fetch HTML via client
4. Measure response time
5. Generate content fingerprint
6. Extract book data
7. Store in MongoDB
8. Update statistics
9. Save checkpoint if interval reached

**Concurrency:**
- Uses `asyncio.Semaphore` to limit concurrent requests
- Default: 10 concurrent book pages
- Configurable via `max_concurrency` setting

#### `async def process_category(category_name: str, category_url: str) -> int`
Processes an entire category including pagination.

**Algorithm:**
```python
1. Fetch category page
2. Extract book URLs from page
3. Crawl all books concurrently (with semaphore)
4. Check for next page
5. If next page exists, repeat from step 1
6. Return total books processed
```

**Logging:**
```
INFO - Processing category: Travel
INFO - Found 20 books on page 1
INFO - Successfully crawled book: The Road to Little Dribbling
INFO - Completed category Travel: 20 books processed
```

### 5. settings.py - Configuration Management

**Purpose**: Centralized configuration using Pydantic settings with `.env` file support.

**Configuration Source:**
Settings are loaded from `.env` file in the project root directory using Pydantic's `BaseSettings` with `model_config = ConfigDict(env_file='.env', extra='allow')`.

**Important:** The crawler **DOES** use the `.env` file for configuration. The `model_config = ConfigDict(env_file='.env', extra='allow')` setting ensures environment variables are loaded from the `.env` file automatically when the `Settings` class is instantiated.

**Available Settings:**

| Setting | Type | Default | Validation | Description |
|---------|------|---------|------------|-------------|
| `mongo_uri` | str | `mongodb://localhost:27017/books` | Valid MongoDB URI | MongoDB connection string |
| `max_concurrency` | int | `10` | 1-20 | Maximum concurrent requests |
| `request_timeout` | int | `10` | 1-60 seconds | HTTP request timeout |
| `retry_attempts` | int | `5` | 1-10 | Number of retry attempts |
| `request_interval` | float | `1.0` | 0.1-10 seconds | Minimum delay between requests |
| `user_agent` | str | `BooksCrawler/1.0 (+https://github.com/crazycoder44/)` | Any string | HTTP User-Agent header |
| `store_html_in_gridfs` | bool | `True` | true/false | Store HTML in GridFS vs filesystem |

**Validation Rules:**
- `max_concurrency`: Prevents overwhelming the server (max 20)
- `request_timeout`: Ensures reasonable timeouts (1-60s range)
- `retry_attempts`: Balances reliability vs performance (max 10)
- `request_interval`: Enforces rate limiting (min 0.1s)

**Usage:**
```python
from crawler.settings import Settings
settings = Settings()  # Automatically loads from .env
print(settings.mongo_uri)
print(settings.max_concurrency)
```

### 6. store.py - MongoDB Storage Layer

**Purpose**: Handles all database operations including storage, deduplication, and change tracking.

**Class: MongoStore**

**Collections:**
1. **books**: Main book data storage
2. **book_changes**: Change history tracking
3. **checkpoints**: Crawler state for resumption
4. **fs.files & fs.chunks**: GridFS for HTML storage (if enabled)

**Key Features:**

#### Content Fingerprinting
Generates SHA-256 hash of HTML content for deduplication:
```python
fingerprint = hashlib.sha256(html.encode('utf-8')).hexdigest()
```

#### Change Detection
Compares current book data with previous version to detect:
- **Price changes**: Tracks increases/decreases
- **Availability changes**: In Stock ↔ Out of Stock
- **Content changes**: Description modifications

**Change Record Structure:**
```python
{
    'book_id': ObjectId('...'),
    'timestamp': datetime.utcnow(),
    'changes': {
        'price_incl_tax': {
            'old': 29.99,
            'new': 24.99,
            'change_percent': -16.67
        },
        'availability': {
            'old': 'In stock (5 available)',
            'new': 'Out of stock'
        }
    }
}
```

#### GridFS Storage
Optional HTML snapshot storage:
```python
if settings.store_html_in_gridfs:
    filename = f"{book_id}_{html_hash}.html"
    grid_out = await self.fs.upload_from_stream(
        filename,
        html.encode('utf-8'),
        metadata={'book_id': book_id, 'hash': html_hash}
    )
```

#### Database Indexes
Optimized indexes for fast queries:
```python
books:
  - source_url (unique): Ensures no duplicate URLs
  - category: Fast category filtering
  - price_incl_tax: Price range queries
  - rating: Rating-based sorting
  - crawl_timestamp: Recent books queries

book_changes:
  - (book_id, timestamp): Change history lookup

checkpoints:
  - checkpoint_type (unique): Single checkpoint per type
```

**Key Methods:**

#### `async def upsert_book(book: Book, html: str) -> str`
Stores or updates book with change detection.

**Process:**
1. Compute HTML hash
2. Store HTML in GridFS (if enabled)
3. Check for existing book by URL
4. If exists:
   - Compare data for changes
   - Record changes in book_changes collection
   - Update book document
5. If new:
   - Insert book document
6. Return book ID

#### `async def save_checkpoint(url: str, metadata: Dict)`
Saves crawler state for resumption.

**Example:**
```python
await store.save_checkpoint(
    url="https://books.toscrape.com/catalogue/book_123/index.html",
    metadata={
        'category': 'Travel',
        'books_processed': 150,
        'categories_completed': 5
    }
)
```

#### `async def find_content_changes(book: Book, html: str) -> Dict`
Identifies specific changes between versions.

**Returns:**
```python
{
    'price_incl_tax': {'old': 29.99, 'new': 24.99},
    'availability': {'old': 'In stock', 'new': 'Out of stock'},
    'description': {'old': '...', 'new': '...'}
}
```

## Prerequisites

### Required Software
- **Python**: 3.8 or higher (tested on 3.10+)
- **MongoDB**: 4.4 or higher (5.0+ recommended)
- **pip**: Latest version

### Python Packages
Core dependencies (see `requirements.txt`):
- `httpx`: Async HTTP client
- `beautifulsoup4`: HTML parsing
- `lxml`: Fast XML/HTML parser
- `motor`: Async MongoDB driver
- `pydantic`: Data validation
- `pydantic-settings`: Settings management
- `tenacity`: Retry logic

### System Requirements
- **RAM**: Minimum 512MB, recommended 1GB
- **Disk**: ~100MB for code + 50MB per 1000 books stored
- **Network**: Stable internet connection
- **MongoDB Storage**: ~50MB per 1000 books (with HTML snapshots)

## Configuration

### Environment Variables Setup

The crawler uses environment variables loaded from a `.env` file in the project root directory. This is handled automatically by Pydantic's `BaseSettings` with the configuration `model_config = ConfigDict(env_file='.env', extra='allow')`.

**Create a `.env` file in the project root:**

```env
# MongoDB Configuration
# Full connection string including database name
mongo_uri=mongodb://localhost:27017/books

# Crawler Performance Settings
max_concurrency=10           # Number of concurrent book page requests (1-20)
request_timeout=10           # HTTP request timeout in seconds (1-60)
retry_attempts=5             # Number of retry attempts on failure (1-10)
request_interval=1.0         # Minimum seconds between requests (0.1-10.0)

# Crawler Identity
user_agent=BooksCrawler/1.0 (+https://github.com/crazycoder44/)

# Storage Options
store_html_in_gridfs=true    # Store HTML snapshots in MongoDB GridFS (true/false)
```

**Configuration Notes:**

1. **mongo_uri**: 
   - Include database name in URI: `mongodb://localhost:27017/books`
   - For authentication: `mongodb://user:pass@localhost:27017/books`
   - For MongoDB Atlas: `mongodb+srv://user:pass@cluster.mongodb.net/books`

2. **max_concurrency**: 
   - Higher values = faster crawling but more server load
   - Recommended: 10 for local testing, 5-8 for production
   - Maximum enforced: 20

3. **request_interval**: 
   - Minimum time between requests to avoid overwhelming server
   - Recommended: 1.0 second for respectful crawling
   - Lower values may trigger rate limiting

4. **store_html_in_gridfs**: 
   - `true`: Store HTML in MongoDB GridFS (better for backups/analysis)
   - `false`: Don't store HTML (saves disk space)
   - GridFS adds ~40KB per book

### Configuration Validation

All settings are validated on startup:
```python
# Invalid configurations will raise ValueError
max_concurrency=25  # Error: must not exceed 20
request_timeout=0   # Error: must be at least 1 second
retry_attempts=-1   # Error: must be at least 1
```

### Default Configuration

If `.env` file is missing or variables are not set, defaults are used:
```python
mongo_uri="mongodb://localhost:27017/books"
max_concurrency=10
request_timeout=10
retry_attempts=5
request_interval=1.0
user_agent="BooksCrawler/1.0 (+https://github.com/crazycoder44/)"
store_html_in_gridfs=True
```

**How .env Loading Works:**

The crawler automatically loads the `.env` file through Pydantic's settings management:

```python
# In settings.py
class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', extra='allow')
    
    mongo_uri: str = "mongodb://localhost:27017/books"
    # ... other settings
```

When `Settings()` is instantiated:
1. Pydantic looks for `.env` file in the current directory
2. Loads all variables from the file
3. Falls back to default values if not found
4. Validates all values according to field validators

**No additional libraries needed** - `pydantic-settings` handles .env file loading natively.

## Data Model

### Complete Book Schema

Books are stored in MongoDB with the following structure:

```python
{
    '_id': ObjectId('507f1f77bcf86cd799439011'),
    'title': 'The Road to Little Dribbling: Adventures of an American in Britain',
    'source_url': 'https://books.toscrape.com/catalogue/the-road-to-little-dribbling_277/index.html',
    'description': 'Twenty years ago, Bill Bryson went on a trip around Britain...',
    'category': 'Travel',
    'price_incl_tax': 23.21,
    'price_excl_tax': 23.21,
    'availability': 'In stock (19 available)',
    'num_reviews': 0,
    'image_url': 'https://books.toscrape.com/media/cache/42/7c/427c9ef3fdb2daf51b7ac6241be3fdbc.jpg',
    'rating': 1,
    'raw_html_hash': 'a1b2c3d4e5f6789...',  # SHA-256 hash
    'raw_html_snapshot_path': 'ObjectId("507f1f77bcf86cd799439012")',  # GridFS reference
    'crawl_timestamp': ISODate('2025-11-09T16:19:41.345Z'),
    'status': 'ok',
    'response_time': 0.234,
    'http_status': 200
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Yes | MongoDB document ID (auto-generated) |
| `title` | string | Yes | Full book title |
| `source_url` | string (URL) | Yes | Original book page URL (unique index) |
| `description` | string | No | Book description/synopsis |
| `category` | string | No | Category name (e.g., "Travel", "Fiction") |
| `price_incl_tax` | float | No | Price including tax in GBP |
| `price_excl_tax` | float | No | Price excluding tax in GBP |
| `availability` | string | No | Stock status text |
| `num_reviews` | integer | No | Number of reviews (≥0) |
| `image_url` | string (URL) | No | Cover image URL |
| `rating` | integer | No | Star rating (0-5) |
| `raw_html_hash` | string | Yes | SHA-256 hash of HTML content |
| `raw_html_snapshot_path` | string | No | GridFS file ID or filesystem path |
| `crawl_timestamp` | datetime | Yes | When the book was crawled |
| `status` | string | Yes | "ok", "error", or "retry" |
| `response_time` | float | No | HTTP request duration in seconds |
| `http_status` | integer | No | HTTP response code (100-599) |

## Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/crazycoder44/web-crawler.git
cd web-crawler
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup MongoDB

**Option A: Local MongoDB**
```bash
# Start MongoDB
mongod --dbpath /path/to/data/directory
```

**Option B: MongoDB Atlas (Cloud)**
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string
4. Add to `.env` file

### Step 5: Configure Environment
```bash
# Create .env file in project root
# Add configuration as shown in Configuration section
```

### Step 6: Initialize Database
```bash
# Test connection
python -m pytest tests/test_connection.py -v
```

## Usage

### Basic Usage

**Run the crawler:**
```bash
python -m tests.test_crawler
```

Or programmatically:
```python
import asyncio
from crawler.runner import BooksCrawler

async def main():
    crawler = BooksCrawler(checkpoint_interval=10)
    stats = await crawler.run()
    print(f"Crawled {stats['total_books']} books")
    print(f"Processed {stats['categories_processed']} categories")

if __name__ == '__main__':
    asyncio.run(main())
```

### Advanced Usage

**Custom configuration:**
```python
from crawler.runner import BooksCrawler

crawler = BooksCrawler(
    start_url="https://books.toscrape.com/",
    checkpoint_interval=20  # Save every 20 books
)

stats = await crawler.run()
```

**Resume from checkpoint:**
```python
crawler = BooksCrawler()
# Automatically resumes from last checkpoint if available
stats = await crawler.run()
```

## Crawler Behavior

### Crawling Strategy

1. **Initialization**: Connects to MongoDB, creates indexes
2. **Category Discovery**: Fetches main page, extracts all 50 categories
3. **Category Processing**: Processes categories sequentially
4. **Book Crawling**: Crawls books concurrently (up to `max_concurrency`)
5. **Completion**: Generates statistics, closes connections

### Deduplication

**URL-based deduplication:**
- Unique index on `source_url` field
- Prevents duplicate entries for same book

**Content-based deduplication:**
- SHA-256 hash of HTML content
- Detects if page content actually changed

### Checkpoint System

Checkpoints enable resumable crawls:

**When checkpoints are saved:**
- Every `checkpoint_interval` books (default: 10)
- At category boundaries
- On graceful shutdown

## Testing

### Run Tests

```bash
# Connection test
python -m pytest tests/test_connection.py -v

# Full crawler test
python -m tests.test_crawler

# All tests
python -m pytest tests/ -v
```

Expected output documented in `tests/README.md`.

## Performance

### Typical Metrics

**Crawl Performance:**
- **Speed**: ~5-8 books/second
- **Duration**: 3-5 minutes for 1000 books
- **Memory**: 100-200MB peak

**MongoDB Storage:**
- **Books only**: ~30KB per book
- **With HTML snapshots**: ~70KB per book

## Error Handling

### Retry Mechanisms

**Automatic retries for:**
- Network errors
- Timeout exceptions
- 5xx server errors

**Retry configuration:**
```python
retry_attempts = 5
wait_exponential(multiplier=1, min=4, max=10)
```

### Error Logging

All errors logged with context. See logs for debugging.

## Advanced Features

### Change Detection

Automatically detects changes between crawls:
- Price changes
- Availability changes
- Content changes

### GridFS Storage

Optional HTML snapshot storage in MongoDB GridFS.

## Troubleshooting

### Common Issues

1. **Connection Refused**: Start MongoDB server
2. **Timeout Errors**: Increase `request_timeout`
3. **Memory Errors**: Reduce `max_concurrency`
4. **Rate Limiting**: Increase `request_interval`

See detailed troubleshooting in documentation.

## Future Improvements

- [ ] Proxy rotation support
- [ ] Adaptive rate limiting
- [ ] Distributed crawling
- [ ] Enhanced data validation
- [ ] Incremental update mode
- [ ] Real-time dashboard

---

**Last Updated**: November 9, 2025  
**Version**: 2.0  
**Repository**: https://github.com/crazycoder44/web-crawler
