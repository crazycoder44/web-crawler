# Books to Scrape API - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
5. [Response Format](#response-format)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Overview

The Books to Scrape API provides programmatic access to a comprehensive catalog of crawled book data. The API supports advanced filtering, sorting, pagination, and change tracking.

**Base URL**: `http://localhost:8000/api/v1`

**Interactive Documentation**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Version**: 1.0.0

---

## Authentication

All endpoints (except `/health`) require API key authentication via the `X-API-Key` HTTP header.

### Obtaining an API Key

Generate a new API key using the provided script:

```bash
python scripts/generate_api_key.py
```

The script will:
1. Generate a secure random API key
2. Create a SHA-256 hash
3. Output the plain key (send to client) and hash (store in `.env`)

### Using Your API Key

Include the API key in the `X-API-Key` header with every request:

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/api/v1/books
```

### Security Notes

- **Never commit API keys** to version control
- Store hashes (not plain keys) in your `.env` file
- Rotate keys periodically for security
- Each key is rate-limited independently

---

## Rate Limiting

The API implements per-key rate limiting to ensure fair usage.

### Limits

- **100 requests per hour** per API key
- Uses sliding window algorithm for accurate tracking
- Automatically cleans up expired entries

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699632000
```

- `X-RateLimit-Limit`: Maximum requests allowed per hour
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### Exceeded Limits

When rate limit is exceeded, you'll receive:

```json
{
  "message": "Rate limit exceeded. Try again later.",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

**HTTP Status**: `429 Too Many Requests`

---

## Endpoints

### 1. List Books

Retrieve a paginated list of books with filtering and sorting.

**Endpoint**: `GET /api/v1/books`

**Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `category` | string | No | Filter by category | `Travel` |
| `min_price` | float | No | Minimum price (inclusive) | `10.0` |
| `max_price` | float | No | Maximum price (inclusive) | `50.0` |
| `rating` | integer | No | Minimum rating (1-5) | `4` |
| `availability` | string | No | Filter by availability text | `In stock` |
| `search` | string | No | Search in title/description | `mystery` |
| `sort_by` | string | No | Sort order | `price_asc` |
| `page` | integer | No | Page number (default: 1) | `1` |
| `limit` | integer | No | Items per page (default: 20, max: 100) | `20` |

**Sort Options**:
- `recent`: Newest first (by crawl timestamp)
- `title`: Alphabetical (A-Z)
- `price_asc`: Lowest price first
- `price_desc`: Highest price first
- `rating_desc`: Highest rating first

**Example Request**:

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/books?category=Travel&min_price=20&sort_by=price_asc&limit=10"
```

**Example Response**:

```json
{
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "A Light in the Attic",
      "description": "It's hard to imagine a world without...",
      "category": "Poetry",
      "price_incl_tax": 51.77,
      "price_excl_tax": 51.77,
      "availability": "In stock (22 available)",
      "rating": 3,
      "num_reviews": 0,
      "image_url": "https://books.toscrape.com/media/cache/fe/72/fe72f0532301ec28892ae79a629a293c.jpg",
      "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
      "crawl_timestamp": "2025-11-10T12:00:00Z"
    }
  ],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  },
  "filters_applied": {
    "category": "Travel",
    "min_price": 20.0,
    "sort_by": "price_asc"
  }
}
```

---

### 2. Get Book by ID

Retrieve detailed information about a specific book.

**Endpoint**: `GET /api/v1/books/{book_id}`

**Path Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `book_id` | string | Yes | MongoDB ObjectId (24-char hex) | `507f1f77bcf86cd799439011` |

**Example Request**:

```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/books/507f1f77bcf86cd799439011
```

**Example Response**:

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "A Light in the Attic",
  "description": "It's hard to imagine a world without A Light in the Attic...",
  "category": "Poetry",
  "price_incl_tax": 51.77,
  "price_excl_tax": 51.77,
  "availability": "In stock (22 available)",
  "rating": 3,
  "num_reviews": 0,
  "image_url": "https://books.toscrape.com/media/cache/fe/72/fe72f0532301ec28892ae79a629a293c.jpg",
  "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "crawl_timestamp": "2025-11-10T12:00:00Z",
  "http_status": 200,
  "response_time": 0.45,
  "status": "success"
}
```

---

### 3. List Changes

Track changes to book data over time (price updates, availability changes, etc.).

**Endpoint**: `GET /api/v1/changes`

**Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `since` | datetime | No | Show changes after this time (ISO 8601) | `2025-11-08T00:00:00Z` |
| `book_id` | string | No | Filter by specific book ID | `507f1f77bcf86cd799439011` |
| `change_type` | string | No | Filter by change type | `update` |
| `page` | integer | No | Page number (default: 1) | `1` |
| `limit` | integer | No | Items per page (default: 20, max: 100) | `20` |

**Example Request**:

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/changes?since=2025-11-08T00:00:00Z&change_type=update&limit=10"
```

**Example Response**:

```json
{
  "data": [
    {
      "id": "673ffbd7c9f2854890e73e51",
      "book_id": "507f1f77bcf86cd799439011",
      "change_type": "update",
      "field_changed": "price_incl_tax",
      "old_value": 51.77,
      "new_value": 48.99,
      "timestamp": "2025-11-10T12:30:00Z",
      "detected_by": "price_monitor"
    },
    {
      "id": "673ffbd7c9f2854890e73e52",
      "book_id": "507f1f77bcf86cd799439012",
      "change_type": "update",
      "field_changed": "availability",
      "old_value": "In stock (5 available)",
      "new_value": "Out of stock",
      "timestamp": "2025-11-10T12:00:00Z",
      "detected_by": "availability_monitor"
    }
  ],
  "pagination": {
    "total": 5551,
    "page": 1,
    "page_size": 20,
    "total_pages": 278,
    "has_next": true,
    "has_prev": false
  },
  "filters_applied": {
    "since": "2025-11-08T00:00:00Z",
    "change_type": "update"
  }
}
```

---

### 4. Health Check

Check API and database health (no authentication required).

**Endpoint**: `GET /health`

**Example Request**:

```bash
curl http://localhost:8000/health
```

**Example Response**:

```json
{
  "status": "healthy",
  "service": "Books to Scrape API",
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "database": "books",
    "collections": 2,
    "books_count": 1000,
    "changes_count": 5551
  }
}
```

---

## Response Format

### Successful Responses

All successful list endpoints return this structure:

```json
{
  "data": [...],           // Array of items
  "pagination": {          // Pagination metadata
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  },
  "filters_applied": {...} // Optional: applied filters
}
```

### Pagination Metadata

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of items matching query |
| `page` | integer | Current page number |
| `page_size` | integer | Number of items per page |
| `total_pages` | integer | Total number of pages |
| `has_next` | boolean | Whether next page exists |
| `has_prev` | boolean | Whether previous page exists |

---

## Error Handling

### Error Response Structure

All errors return this consistent format:

```json
{
  "message": "Error description",
  "details": {             // Optional: detailed error info
    "field": "error detail"
  },
  "timestamp": "2025-11-10T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error (invalid parameters) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Common Error Examples

**Missing API Key (401)**:
```json
{
  "message": "Missing API key",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

**Invalid API Key (401)**:
```json
{
  "message": "Invalid API key",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

**Validation Error (422)**:
```json
{
  "message": "Validation error",
  "details": {
    "page": "must be >= 1",
    "rating": "must be between 1 and 5"
  },
  "timestamp": "2025-11-10T12:00:00Z"
}
```

**Not Found (404)**:
```json
{
  "message": "Book with ID '507f1f77bcf86cd799439011' not found",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

**Rate Limit Exceeded (429)**:
```json
{
  "message": "Rate limit exceeded. Try again later.",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

---

## Examples

### Complete Usage Examples

#### 1. List All Books (First Page)

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/books
```

#### 2. Search for Travel Books Under $30

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/books?category=Travel&max_price=30&sort_by=price_asc"
```

#### 3. Find Highly-Rated Mystery Books

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/books?category=Mystery&rating=4&sort_by=rating_desc"
```

#### 4. Search Books by Title

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/books?search=sapiens&limit=5"
```

#### 5. Get Specific Book Details

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/books/507f1f77bcf86cd799439011
```

#### 6. Track Recent Price Changes

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/changes?since=2025-11-08T00:00:00Z&change_type=update"
```

#### 7. Monitor Changes for Specific Book

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/changes?book_id=507f1f77bcf86cd799439011"
```

#### 8. Check API Health

```bash
curl http://localhost:8000/health
```

### Python Example

```python
import requests

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your-api-key-here"

headers = {"X-API-Key": API_KEY}

# List travel books under $50
response = requests.get(
    f"{API_BASE_URL}/books",
    headers=headers,
    params={
        "category": "Travel",
        "max_price": 50,
        "sort_by": "price_asc",
        "limit": 10
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['pagination']['total']} travel books")
    
    for book in data['data']:
        print(f"- {book['title']}: ${book['price_incl_tax']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### JavaScript Example

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'your-api-key-here';

// Search for highly-rated books
async function searchBooks() {
  const response = await fetch(
    `${API_BASE_URL}/books?rating=4&sort_by=rating_desc&limit=10`,
    {
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );
  
  if (response.ok) {
    const data = await response.json();
    console.log(`Found ${data.pagination.total} books`);
    
    data.data.forEach(book => {
      console.log(`${book.title} - Rating: ${book.rating}/5`);
    });
  } else {
    const error = await response.json();
    console.error('Error:', error.message);
  }
}

searchBooks();
```

---

## Best Practices

1. **Always include your API key** in the `X-API-Key` header
2. **Check rate limit headers** to avoid hitting limits
3. **Use pagination** for large result sets (don't request everything at once)
4. **Filter early** to reduce response sizes and improve performance
5. **Handle errors gracefully** and check HTTP status codes
6. **Cache responses** when appropriate to reduce API calls
7. **Use ISO 8601 format** for datetime parameters
8. **Validate ObjectIds** before making requests (24-char hex strings)

---

## Support & Resources

- **GitHub Repository**: https://github.com/crazycoder44/web-crawler
- **Issues**: Report bugs or request features via GitHub Issues
- **Interactive Documentation**: http://localhost:8000/docs (when running locally)

---

*Last Updated: November 10, 2025 | API Version: 1.0.0*
