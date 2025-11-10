"""
FastAPI Application Entry Point

This module initializes the FastAPI application with all routes, middleware,
and lifecycle event handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import configuration
from src.api.settings import settings

# Import database lifecycle
from src.utils.database import connect_to_mongo, close_mongo_connection

# Import routes
from src.api.routes import health, books, changes

# Import middleware
from src.api.middleware.rate_limiter import RateLimitMiddleware, start_cleanup_task
from src.api.middleware.logging_middleware import RequestLoggingMiddleware

# Import exception handlers
from src.api.exception_handlers import register_exception_handlers

# Import enhanced logging
from src.utils.logging import setup_logging

# Configure enhanced logging (Step 12)
setup_logging(
    log_level=settings.api_log_level,
    enable_console=True,
    enable_file=settings.log_to_file,
    enable_json=settings.log_json_format,
    enable_rotation=settings.log_rotation
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with enhanced OpenAPI documentation
app = FastAPI(
    title=settings.api_title,
    description=f"""
## {settings.api_description}

### 🔐 Authentication

All endpoints (except `/health`) require API key authentication via the `X-API-Key` header.

**Header Format:**
```
X-API-Key: your-api-key-here
```

To obtain an API key, contact your system administrator or generate one using:
```bash
python scripts/generate_api_key.py
```

### 📊 Rate Limiting

- **Limit:** {settings.rate_limit_per_hour} requests per hour per API key
- **Headers:** Rate limit info included in response headers:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

### 📖 Available Endpoints

- **GET /api/v1/books** - List all books with filtering and pagination
- **GET /api/v1/books/{{id}}** - Get detailed information about a specific book
- **GET /api/v1/changes** - Track changes to book data over time
- **GET /health** - Health check endpoint (no authentication required)

### 🔍 Filtering & Sorting

Books endpoint supports advanced filtering:
- Category, price range, rating, availability
- Full-text search across title and description
- Multiple sort options (recent, title, price, rating)

### 📄 Response Format

All successful responses follow this structure:
```json
{{
  "data": [...],
  "pagination": {{
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  }}
}}
```

### ⚠️ Error Responses

Errors return consistent structure with HTTP status codes:
- **400** - Bad Request
- **401** - Unauthorized (missing/invalid API key)
- **404** - Resource Not Found
- **422** - Validation Error
- **429** - Rate Limit Exceeded
- **500** - Internal Server Error
""",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "API Support",
        "url": "https://github.com/crazycoder44/web-crawler",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Books",
            "description": "Operations related to querying book data. Includes listing books with filters, sorting, pagination, and retrieving individual book details."
        },
        {
            "name": "Changes",
            "description": "Track changes to book data over time. Monitor price updates, availability changes, and other modifications with timestamp-based filtering."
        },
        {
            "name": "Health",
            "description": "System health and monitoring endpoints. Check API availability and database connectivity without authentication."
        }
    ]
)

# CORS Middleware (configured from settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request Logging Middleware (Step 12)
app.add_middleware(RequestLoggingMiddleware)

# Rate Limiting Middleware (per API key)
app.add_middleware(RateLimitMiddleware)

# Register global exception handlers
register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Initializes:
    - Database connections
    - Logging configuration
    - Cache warmup (if needed)
    """
    logger.info(f"Starting {settings.api_title} v{settings.api_version}...")
    logger.info(f"Server: {settings.api_host}:{settings.api_port}")
    logger.info(f"CORS Origins: {settings.parsed_allowed_origins}")
    logger.info(f"Rate Limit: {settings.rate_limit_per_hour} req/hour")
    
    # Connect to MongoDB
    try:
        await connect_to_mongo()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        logger.warning("API will start but database operations will fail")
    
    # Start rate limit cleanup task
    try:
        await start_cleanup_task()
        logger.info("✅ Rate limit cleanup task started")
    except Exception as e:
        logger.error(f"❌ Failed to start cleanup task: {e}")
    
    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    Cleanup tasks:
    - Close database connections
    - Flush logs
    - Clean up resources
    """
    logger.info(f"Shutting down {settings.api_title}...")
    await close_mongo_connection()
    logger.info("API shutdown complete")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information and status.
    
    Returns:
        dict: API metadata and available endpoints
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "books": "/books",
            "changes": "/changes"
        },
        "authentication": "API Key required (X-API-Key header)"
    }


# Register routers
app.include_router(health.router)
app.include_router(books.router, prefix="/api/v1")
app.include_router(changes.router, prefix="/api/v1")

# Register exception handlers (Step 10)
# register_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration with settings
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Auto-reload on code changes
        log_level=settings.api_log_level.lower()
    )

