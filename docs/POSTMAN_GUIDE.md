# Postman Collection Guide

## 📦 Books to Scrape API - Postman Collection

This guide explains how to import and use the Postman collection for the Books to Scrape API.

---

## 📋 Contents

1. [What's Included](#whats-included)
2. [Installation & Setup](#installation--setup)
3. [Environment Variables](#environment-variables)
4. [Collection Structure](#collection-structure)
5. [Running Requests](#running-requests)
6. [Running Tests](#running-tests)
7. [Troubleshooting](#troubleshooting)

---

## 🎁 What's Included

### Files

- **`Books_API_Postman_Collection.json`**: Complete API collection with 40+ requests
- **`Books_API_Environment_Local.json`**: Local development environment
- **`Books_API_Environment_Production.json`**: Production environment template

### Collection Features

- ✅ All 4 API endpoints (Health, Books, Book Detail, Changes)
- ✅ 40+ example requests with various filters and parameters
- ✅ Automated test scripts (100+ assertions)
- ✅ Rate limiting tests
- ✅ Authentication tests
- ✅ Error handling tests
- ✅ Environment variable support

---

## 🚀 Installation & Setup

### Step 1: Import Collection

1. Open Postman
2. Click **Import** button (top left)
3. Select **Upload Files**
4. Choose `Books_API_Postman_Collection.json`
5. Click **Import**

### Step 2: Import Environment

1. Click **Import** again
2. Select `Books_API_Environment_Local.json`
3. Click **Import**
4. (Optional) Import `Books_API_Environment_Production.json` for production use

### Step 3: Set Active Environment

1. Click the environment dropdown (top right)
2. Select **"Books API - Local Development"**

### Step 4: Configure API Key

1. Click the **eye icon** (👁️) next to the environment dropdown
2. Click **Edit** for your environment
3. Set the `api_key` value to your actual API key
4. Click **Save**

**Generate an API key** if you don't have one:

```bash
# Run from project directory
python scripts/generate_api_key.py
```

---

## ⚙️ Environment Variables

### Available Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `base_url` | string | API base URL | `http://localhost:8000` |
| `api_key` | secret | Your API key for authentication | `your-api-key-here` |
| `book_id` | string | Book ID (auto-populated) | `507f1f77bcf86cd799439011` |
| `rate_limit_remaining` | string | Remaining requests (auto-tracked) | `95` |

### Local Development

```json
{
  "base_url": "http://localhost:8000",
  "api_key": "your-local-api-key"
}
```

### Production

```json
{
  "base_url": "https://api.yourdomain.com",
  "api_key": "your-production-api-key"
}
```

---

## 📂 Collection Structure

### 1. Health Check (1 request)

- **Health Check - No Auth Required**: Check API status

### 2. Books (14 requests)

- **Get All Books - Default**: List all books with default pagination
- **Get Books - With Pagination**: Custom page and limit
- **Search Books by Title**: Full-text search
- **Filter Books by Category**: Filter by category
- **Filter Books by Price Range**: Filter by min/max price
- **Filter Books by Rating**: Filter by rating (1-5)
- **Filter Books by Availability**: Filter by in_stock status
- **Sort Books by Price (Ascending)**: Sort by price low to high
- **Sort Books by Price (Descending)**: Sort by price high to low
- **Sort Books by Title**: Alphabetical sorting
- **Sort Books by Rating**: Sort by highest rated
- **Sort Books by Most Recent**: Sort by last_updated
- **Complex Query - Multiple Filters**: Combine multiple filters
- **Get Book by ID**: Get specific book details
- **Get Book by Invalid ID**: Error handling test

### 3. Changes (9 requests)

- **Get All Changes - Default**: List all tracked changes
- **Get Changes - With Pagination**: Custom pagination
- **Get Changes for Specific Book**: Filter by book_id
- **Get Changes Since Timestamp**: Filter by start date
- **Get Changes Until Timestamp**: Filter by end date
- **Get Changes in Time Range**: Filter by date range
- **Filter Changes by Type**: Filter by change_type (insert/update/delete)
- **Filter Changes by Field**: Filter by field_changed
- **Complex Changes Query**: Combine multiple filters

### 4. Authentication & Rate Limiting (4 requests)

- **Missing API Key**: Test 401 error when no key provided
- **Invalid API Key**: Test 401 error with invalid key
- **Check Rate Limit Headers**: Verify rate limit headers
- **Verify Rate Limit Decrements**: Test rate limit counter

### 5. Error Handling (6 requests)

- **Invalid Page Number**: Test validation error (page >= 1)
- **Invalid Limit**: Test validation error (limit <= 100)
- **Invalid Rating**: Test validation error (rating 1-5)
- **Invalid Sort Option**: Test validation error
- **Invalid Timestamp Format**: Test ISO 8601 validation
- **Invalid Book ID Format**: Test ObjectId validation

---

## 🎯 Running Requests

### Individual Request

1. Select a request from the collection
2. Click **Send**
3. View response in the bottom panel
4. Check the **Test Results** tab for assertions

### Folder (Run All Requests)

1. Right-click on a folder (e.g., "Books")
2. Select **Run folder**
3. Click **Run Books** in the Collection Runner
4. View aggregated test results

### Entire Collection

1. Click the **three dots** (•••) next to the collection name
2. Select **Run collection**
3. Configure iterations and delay if needed
4. Click **Run Books to Scrape API**
5. View comprehensive test report

---

## ✅ Running Tests

### Automated Tests

Each request includes automated test scripts that verify:

- ✅ HTTP status codes (200, 401, 404, 422, 429)
- ✅ Response structure (required fields)
- ✅ Data types and formats
- ✅ Business logic (filters, sorting, pagination)
- ✅ Rate limiting headers
- ✅ Error messages

### Example Test Results

```
✓ Status code is 200
✓ Response has pagination metadata
✓ Items array is not empty
✓ Each book has required fields
✓ Rate limit headers are present
✓ Response time is less than 500ms
```

### Test Script Examples

#### Basic Status Check

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});
```

#### Validate Response Structure

```javascript
pm.test("Response has pagination metadata", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('items');
    pm.expect(jsonData).to.have.property('total');
    pm.expect(jsonData).to.have.property('page');
});
```

#### Validate Business Logic

```javascript
pm.test("All books within price range", function () {
    var jsonData = pm.response.json();
    jsonData.items.forEach(book => {
        pm.expect(book.price).to.be.at.least(10.0);
        pm.expect(book.price).to.be.at.most(30.0);
    });
});
```

---

## 🔧 Troubleshooting

### Issue 1: "Missing API Key" Error

**Error**: `401 Unauthorized - Missing API key`

**Solution**:
1. Ensure environment is selected (top right dropdown)
2. Check that `api_key` variable is set in environment
3. Verify the API key is correct
4. Ensure the key is in the `X-API-Key` header (check request headers)

### Issue 2: "Invalid API Key" Error

**Error**: `401 Unauthorized - Invalid API key`

**Solution**:
1. Generate a new API key: `python scripts/generate_api_key.py`
2. Add the hash to `.env` file on the server
3. Update `api_key` in Postman environment with the **plain key**
4. Restart the API server to reload environment variables

### Issue 3: "Connection Refused"

**Error**: `Could not send request`

**Solution**:
1. Verify API server is running: `uvicorn api.main:app`
2. Check `base_url` in environment matches server address
3. Ensure port 8000 is not blocked by firewall
4. Test health check endpoint: `http://localhost:8000/health`

### Issue 4: Rate Limit Exceeded

**Error**: `429 Too Many Requests`

**Solution**:
1. Wait for rate limit to reset (check `X-RateLimit-Reset` header)
2. Use a different API key
3. Increase `RATE_LIMIT_PER_HOUR` in `.env` (development only)
4. Space out requests in Collection Runner

### Issue 5: "book_id" Variable Not Set

**Error**: Request fails because `{{book_id}}` is empty

**Solution**:
1. Run "Get All Books - Default" request first
2. This will automatically set `book_id` from the first result
3. Or manually set `book_id` in environment variables

### Issue 6: Tests Failing

**Issue**: Some tests fail even with 200 status

**Solution**:
1. Check if database has data (run crawler first)
2. Verify filter values match data in database
3. Some tests expect specific data (e.g., category "Fiction")
4. Adjust test parameters to match your data

---

## 📊 Collection Runner Tips

### Run with Delays

Add delay between requests to avoid rate limiting:

1. Open Collection Runner
2. Set **Delay** to `1000ms` (1 second)
3. Click **Run**

### Save Responses

Save responses for debugging:

1. In Collection Runner, enable **Save responses**
2. Run collection
3. Click on failed requests to see full response

### Data-Driven Testing

Use CSV/JSON data files for parameterized tests:

1. Click **Select File** in Collection Runner
2. Choose a CSV file with test data
3. Use `{{column_name}}` in requests
4. Run collection with multiple iterations

---

## 🎓 Best Practices

### 1. Use Environment Variables

Always use `{{base_url}}` and `{{api_key}}` instead of hardcoding:

```
✅ Good: {{base_url}}/api/v1/books
❌ Bad:  http://localhost:8000/api/v1/books
```

### 2. Run Health Check First

Always start by running the Health Check to verify API is running:

```
Health Check - No Auth Required → Should return 200 OK
```

### 3. Set book_id Early

Run "Get All Books - Default" early to populate `book_id` for other requests.

### 4. Monitor Rate Limits

Check `X-RateLimit-Remaining` header to avoid hitting limits:

```javascript
console.log("Remaining requests:", pm.response.headers.get('X-RateLimit-Remaining'));
```

### 5. Use Folders for Organization

Run related tests together by using folders:

- Run "Books" folder to test all book endpoints
- Run "Authentication & Rate Limiting" to test security
- Run "Error Handling" to test validation

---

## 📝 Customizing Requests

### Add Custom Headers

1. Select a request
2. Go to **Headers** tab
3. Add custom headers as needed

### Modify Query Parameters

1. Select a request
2. Go to **Params** tab
3. Check/uncheck parameters or change values
4. URL updates automatically

### Edit Request Body

For POST/PUT requests (if added later):

1. Go to **Body** tab
2. Select format (JSON, form-data, etc.)
3. Edit request body
4. Click **Send**

---

## 🔐 Security Notes

### Production Use

- ✅ Always use HTTPS in production (`https://api.yourdomain.com`)
- ✅ Keep API keys secret (mark as "secret" type in environment)
- ✅ Never commit API keys to version control
- ✅ Rotate API keys regularly
- ✅ Use different keys for different environments

### Sharing Collections

When sharing the collection:

- ❌ Don't include API keys in the collection file
- ✅ Share environment file with empty `api_key` value
- ✅ Provide instructions for generating keys
- ✅ Use collection variables for base_url, not hardcoded values

---

## 📚 Additional Resources

- **API Documentation**: See `API_DOCUMENTATION.md`
- **Project README**: See `README.md`
- **OpenAPI Docs**: http://localhost:8000/docs (when server is running)
- **ReDoc**: http://localhost:8000/redoc

---

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review API logs in `logs/` directory
3. Test with curl commands first to isolate Postman issues
4. Open an issue on GitHub with collection export and error details

---

*Last Updated: November 10, 2025 | Version: 1.0.0*
