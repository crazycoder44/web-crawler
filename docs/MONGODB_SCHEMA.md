# MongoDB Schema Documentation

## Database Overview

The web crawler application uses MongoDB to store crawled book data, change history, scheduling information, and API keys.

**Database Name**: `web_crawler_db` (configurable via `MONGO_DB_NAME` environment variable)

---

## Collections

### 1. `books` Collection

Stores information about books crawled from the website.

#### Schema

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  url: String,                      // Source URL (unique index)
  title: String,                    // Book title (indexed)
  price: Decimal128,                // Current price
  availability: String,             // Availability status
  rating: Number,                   // Rating (0-5)
  num_reviews: Number,              // Number of reviews
  description: String,              // Book description
  upc: String,                      // Universal Product Code (unique index)
  category: String,                 // Book category (indexed)
  product_type: String,             // Product classification
  price_excl_tax: Decimal128,       // Price excluding tax
  price_incl_tax: Decimal128,       // Price including tax
  tax: Decimal128,                  // Tax amount
  num_available: Number,            // Number of items in stock
  image_url: String,                // Product image URL
  crawled_at: Date,                 // Timestamp of crawl (indexed)
  last_updated: Date,               // Last modification timestamp
  fingerprint: String               // Change detection fingerprint
}
```

#### Indexes

- `url`: unique, ascending
- `upc`: unique, ascending
- `title`: text index
- `category`: ascending
- `crawled_at`: descending
- Compound index: `{category: 1, crawled_at: -1}`

#### Sample Document

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "title": "A Light in the Attic",
  "price": 51.77,
  "availability": "In stock",
  "rating": 3,
  "num_reviews": 0,
  "description": "A collection of poems and drawings...",
  "upc": "a897fe39b1053632",
  "category": "Poetry",
  "product_type": "Books",
  "price_excl_tax": 51.77,
  "price_incl_tax": 51.77,
  "tax": 0.00,
  "num_available": 22,
  "image_url": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
  "crawled_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:30:00Z",
  "fingerprint": "a1b2c3d4e5f6..."
}
```

---

### 2. `change_history` Collection

Tracks changes to book data over time for change detection and reporting.

#### Schema

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  url: String,                      // Book URL (indexed)
  upc: String,                      // Book UPC (indexed)
  title: String,                    // Book title
  change_type: String,              // Type: "price", "availability", "content"
  field_name: String,               // Changed field name
  old_value: Mixed,                 // Previous value
  new_value: Mixed,                 // New value
  detected_at: Date,                // Change detection timestamp (indexed)
  severity: String,                 // "low", "medium", "high"
  notified: Boolean,                // Email notification sent flag
  notified_at: Date                 // Notification timestamp
}
```

#### Indexes

- `url`: ascending
- `upc`: ascending
- `detected_at`: descending
- Compound index: `{url: 1, detected_at: -1}`
- Compound index: `{change_type: 1, detected_at: -1}`

#### Sample Document

```json
{
  "_id": "507f1f77bcf86cd799439012",
  "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "upc": "a897fe39b1053632",
  "title": "A Light in the Attic",
  "change_type": "price",
  "field_name": "price",
  "old_value": 51.77,
  "new_value": 45.50,
  "detected_at": "2024-01-16T14:20:00Z",
  "severity": "medium",
  "notified": true,
  "notified_at": "2024-01-16T14:25:00Z"
}
```

---

### 3. `crawl_runs` Collection

Records information about crawler execution runs for monitoring and reporting.

#### Schema

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  run_id: String,                   // Unique run identifier (indexed)
  start_time: Date,                 // Crawl start timestamp
  end_time: Date,                   // Crawl end timestamp
  status: String,                   // "running", "completed", "failed"
  total_pages: Number,              // Total pages crawled
  total_books: Number,              // Total books processed
  new_books: Number,                // New books added
  updated_books: Number,            // Existing books updated
  errors: Array,                    // Error messages
  duration_seconds: Number,         // Total execution time
  crawler_config: Object            // Configuration snapshot
}
```

#### Indexes

- `run_id`: unique, ascending
- `start_time`: descending
- `status`: ascending

#### Sample Document

```json
{
  "_id": "507f1f77bcf86cd799439013",
  "run_id": "crawl_20240115_103000",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": "2024-01-15T11:45:00Z",
  "status": "completed",
  "total_pages": 50,
  "total_books": 1000,
  "new_books": 50,
  "updated_books": 20,
  "errors": [],
  "duration_seconds": 4500,
  "crawler_config": {
    "max_concurrent": 10,
    "delay": 1.0,
    "user_agent": "CustomCrawler/1.0"
  }
}
```

---

### 4. `api_keys` Collection

Stores API keys for authentication and rate limiting.

#### Schema

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  key: String,                      // API key (unique, hashed, indexed)
  name: String,                     // Key name/description
  created_at: Date,                 // Creation timestamp
  last_used: Date,                  // Last usage timestamp
  is_active: Boolean,               // Active status (indexed)
  rate_limit: Number,               // Requests per minute
  permissions: Array,               // Permission scopes
  metadata: Object                  // Additional key metadata
}
```

#### Indexes

- `key`: unique, ascending
- `is_active`: ascending
- `created_at`: descending

#### Sample Document

```json
{
  "_id": "507f1f77bcf86cd799439014",
  "key": "hashed_api_key_value",
  "name": "Production API Key",
  "created_at": "2024-01-01T00:00:00Z",
  "last_used": "2024-01-15T10:30:00Z",
  "is_active": true,
  "rate_limit": 100,
  "permissions": ["read", "write"],
  "metadata": {
    "owner": "system",
    "environment": "production"
  }
}
```

---

### 5. `scheduled_jobs` Collection

Manages scheduled crawler jobs and their execution history.

#### Schema

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  job_id: String,                   // Job identifier (indexed)
  job_type: String,                 // "crawler", "report", "cleanup"
  schedule: String,                 // Cron expression
  is_active: Boolean,               // Job active status
  last_run: Date,                   // Last execution timestamp
  next_run: Date,                   // Next scheduled run (indexed)
  run_count: Number,                // Total execution count
  failure_count: Number,            // Total failure count
  config: Object,                   // Job-specific configuration
  created_at: Date,                 // Job creation timestamp
  updated_at: Date                  // Last modification timestamp
}
```

#### Indexes

- `job_id`: unique, ascending
- `next_run`: ascending
- `is_active`: ascending

#### Sample Document

```json
{
  "_id": "507f1f77bcf86cd799439015",
  "job_id": "daily_crawl",
  "job_type": "crawler",
  "schedule": "0 2 * * *",
  "is_active": true,
  "last_run": "2024-01-15T02:00:00Z",
  "next_run": "2024-01-16T02:00:00Z",
  "run_count": 150,
  "failure_count": 2,
  "config": {
    "full_crawl": true,
    "categories": ["Fiction", "Poetry"]
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T02:00:00Z"
}
```

---

## Data Relationships

### Book → Change History
- One-to-Many: Each book can have multiple change history records
- Linked by: `url` and `upc` fields

### Crawl Runs → Books
- One-to-Many: Each crawl run processes multiple books
- Linked by: `crawled_at` timestamp correlation

### Scheduled Jobs → Crawl Runs
- One-to-Many: Each scheduled job creates multiple crawl runs
- Linked by: `job_id` reference in crawl run metadata

---

## Connection Configuration

### Environment Variables

```bash
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=web_crawler_db
MONGO_USER=admin
MONGO_PASSWORD=secure_password
MONGO_AUTH_SOURCE=admin
```

### Connection String Format

```
mongodb://[username:password@]host[:port][/database][?options]
```

### Example Connection Strings

**Local Development:**
```
mongodb://localhost:27017/web_crawler_db
```

**Production with Authentication:**
```
mongodb://admin:password@prod-server:27017/web_crawler_db?authSource=admin
```

**MongoDB Atlas:**
```
mongodb+srv://user:password@cluster.mongodb.net/web_crawler_db?retryWrites=true&w=majority
```

---

## Database Maintenance

### Recommended Index Maintenance

```javascript
// Check index usage
db.books.aggregate([{ $indexStats: {} }])

// Rebuild indexes if needed
db.books.reIndex()
```

### Data Retention Policies

- **Change History**: Retain for 90 days, archive older records
- **Crawl Runs**: Retain for 30 days
- **API Keys**: Keep indefinitely, mark inactive as needed

### Backup Strategy

- Daily automated backups using `mongodump`
- Retain backups for 7 days
- Weekly full backup retained for 4 weeks

---

## Performance Considerations

### Collection Size Estimates

| Collection | Estimated Documents | Index Size | Data Size |
|------------|---------------------|------------|-----------|
| books | 10,000 - 50,000 | ~10 MB | ~50 MB |
| change_history | 50,000 - 200,000 | ~20 MB | ~100 MB |
| crawl_runs | 1,000 - 5,000 | ~1 MB | ~5 MB |
| api_keys | 10 - 100 | <1 MB | <1 MB |
| scheduled_jobs | 5 - 50 | <1 MB | <1 MB |

### Query Optimization Tips

1. Always use indexed fields in queries
2. Limit result sets with `.limit()`
3. Use projection to return only needed fields
4. Leverage compound indexes for multi-field queries
5. Monitor slow queries with profiling

---

## Migration and Versioning

### Schema Version

Current schema version: **1.0.0**

### Migration Scripts

Migration scripts located in: `scripts/migrations/`

To apply migrations:
```bash
python scripts/migrations/apply_migrations.py
```

---

## Security Considerations

- API keys stored as hashed values
- Database credentials stored in environment variables
- MongoDB authentication enabled in production
- Network access restricted via firewall rules
- Regular security audits and updates

---

*Last updated: 2024-01-15*
