# Books Crawler

A robust, asynchronous web crawler designed to extract book information from [Books to Scrape](https://books.toscrape.com/), implementing pagination handling and category-based crawling with MongoDB storage.

## Features

- ✨ Asynchronous crawling with concurrency control
- 📚 Category-based book extraction
- 💾 MongoDB storage with deduplication
- 🔄 Checkpoint system for resumable crawls
- 📊 Detailed logging and statistics
- ⚡ Rate limiting and request throttling
- 🛡️ Error handling and retry mechanisms

## Architecture

The crawler is composed of several key components:

- `client.py`: Handles HTTP requests with rate limiting and retries
- `models.py`: Defines data models for books and other entities
- `parsers.py`: Contains HTML parsing logic for extracting book information
- `runner.py`: Implements the main crawler execution logic
- `settings.py`: Manages configuration and environment variables
- `store.py`: Handles MongoDB database operations

## Prerequisites

- Python 3.10 or higher
- MongoDB 4.4 or higher
- Required Python packages (see requirements.txt)

## Configuration

The crawler uses environment variables for configuration. Create a `.env` file with:

```env
mongo_uri=mongodb://localhost:27017/books
max_concurrency=10
request_timeout=10
retry_attempts=5
user_agent=BooksCrawler/1.0 (+https://github.com/your-github-username/)
store_html_in_gridfs=true
```

## Testing

### 1. Test Database Connection

First, ensure MongoDB is running and test the connection:

```bash
python -m tests.test_connection
```

Expected output:
```
INFO: MongoDB connection successful
INFO: Database name: books
INFO: Collections: ['books', 'raw_html']
```

### 2. Test Crawler

Run the crawler test which will attempt to crawl all books:

```bash
python -m tests.test_crawler
```

The test will:
- Crawl all book categories
- Extract and store book information
- Save raw HTML content
- Generate crawl statistics

## Data Model

Books are stored with the following structure:

```python
{
    'title': str,
    'source_url': HttpUrl,
    'description': Optional[str],
    'category': str,
    'price_incl_tax': float,
    'price_excl_tax': float,
    'availability': str,
    'num_reviews': int,
    'image_url': HttpUrl,
    'rating': int,
    'fingerprint': str,
    'crawl_timestamp': datetime,
    'status': str,
    'http_status': int
}
```

## Crawler Behavior

1. **Category Discovery**:
   - Starts from the main index page
   - Extracts all book categories
   - Processes each category sequentially

2. **Book Processing**:
   - Extracts books from category pages
   - Handles pagination within categories
   - Processes book detail pages concurrently (controlled by MAX_CONCURRENCY)

3. **Data Storage**:
   - Deduplicates books using content fingerprinting
   - Stores raw HTML for future reference
   - Creates checkpoints for resumable operations

4. **Error Handling**:
   - Retries failed requests
   - Logs errors for debugging
   - Maintains crawl statistics

## Statistics and Logging

The crawler generates detailed statistics including:
- Total books crawled
- Categories processed
- Success/failure counts
- Duration of crawl
- Price and rating distributions

Logs are stored with timestamps and contain:
- Crawl progress information
- HTTP request details
- Error messages and stack traces
- Checkpoint creation events

## Performance

Typical performance metrics:
- Crawl speed: ~5 books/second
- Average crawl time: 3-4 minutes for 1000 books
- Memory usage: ~100MB
- Network efficiency: Respects rate limits

## Error Recovery

The crawler implements several recovery mechanisms:
- Automatic retry on failed requests
- Checkpoint-based resume capability
- Transaction-based MongoDB operations
- Connection pool management

## Future Improvements

- [ ] Add support for proxy rotation
- [ ] Implement adaptive rate limiting
- [ ] Add support for distributed crawling
- [ ] Enhance data validation and cleaning
- [ ] Add support for incremental updates