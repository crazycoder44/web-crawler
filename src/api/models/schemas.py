"""
API Request and Response Schemas

Pydantic models for request validation and response serialization.
These models ensure type safety, validation, and automatic OpenAPI documentation.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from bson import ObjectId


# ==================== Custom Types ====================

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        """Pydantic v2 compatibility."""
        from pydantic_core import core_schema
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
        )


# ==================== Error Response ====================

class ErrorResponse(BaseModel):
    """
    Standard error response format for all API errors.
    
    Attributes:
        status: Response status (always "error")
        message: Human-readable error message
        details: Optional additional error details or validation errors
        timestamp: When the error occurred
    
    Example:
        {
            "status": "error",
            "message": "Book not found",
            "details": {"book_id": "invalid_id"},
            "timestamp": "2025-11-09T20:00:00Z"
        }
    """
    status: str = Field(default="error", description="Response status")
    message: str = Field(..., description="Error message", example="Resource not found")
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional error details",
        example={"field": "book_id", "reason": "Invalid format"}
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "error",
                "message": "Invalid API key",
                "details": {"header": "X-API-Key"},
                "timestamp": "2025-11-09T20:00:00Z"
            }
        }
    }


# ==================== Pagination ====================

class PaginationMeta(BaseModel):
    """
    Pagination metadata for list responses.
    
    Attributes:
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
    """
    total: int = Field(..., description="Total number of items", example=1000, ge=0)
    page: int = Field(..., description="Current page number", example=1, ge=1)
    page_size: int = Field(..., description="Items per page", example=20, ge=1, le=100)
    total_pages: int = Field(..., description="Total number of pages", example=50, ge=0)
    has_next: bool = Field(..., description="Has next page", example=True)
    has_prev: bool = Field(..., description="Has previous page", example=False)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 1000,
                "page": 1,
                "page_size": 20,
                "total_pages": 50,
                "has_next": True,
                "has_prev": False
            }
        }
    }


# ==================== Book Models ====================

class BookResponse(BaseModel):
    """
    Book response model representing a single book from the catalog.
    
    Attributes:
        id: Unique MongoDB ObjectId
        source_url: Original URL from books.toscrape.com
        title: Book title
        description: Full book description
        category: Book category/genre
        price_incl_tax: Price including tax
        price_excl_tax: Price excluding tax
        availability: Availability status (e.g., "3 available")
        num_reviews: Number of reviews
        image_url: Book cover image URL
        rating: Star rating (1-5)
        raw_html_hash: SHA-256 hash of the raw HTML
        raw_html_snapshot_path: GridFS path to HTML snapshot
        crawl_timestamp: When the book was crawled
        status: Crawl status (success, error, retry)
        response_time: HTTP response time in seconds
        http_status: HTTP status code
    """
    id: str = Field(..., alias="_id", description="Unique book ID")
    source_url: str = Field(..., description="Original book URL", example="https://books.toscrape.com/catalogue/book_123/index.html")
    title: str = Field(..., description="Book title", example="The Great Gatsby")
    description: Optional[str] = Field(None, description="Book description")
    category: Optional[str] = Field(None, description="Book category", example="Fiction")
    price_incl_tax: Optional[float] = Field(None, description="Price including tax", example=19.99, ge=0)
    price_excl_tax: Optional[float] = Field(None, description="Price excluding tax", example=19.99, ge=0)
    availability: Optional[str] = Field(None, description="Availability status", example="In stock (22 available)")
    num_reviews: Optional[int] = Field(None, description="Number of reviews", example=5, ge=0)
    image_url: Optional[str] = Field(None, description="Book cover image URL")
    rating: Optional[int] = Field(None, description="Star rating (1-5)", example=4, ge=0, le=5)
    raw_html_hash: Optional[str] = Field(None, description="SHA-256 hash of raw HTML")
    raw_html_snapshot_path: Optional[str] = Field(None, description="GridFS path to HTML snapshot")
    crawl_timestamp: datetime = Field(..., description="When the book was crawled")
    status: Optional[str] = Field(None, description="Crawl status", example="success")
    response_time: Optional[float] = Field(None, description="HTTP response time (seconds)", example=0.5, ge=0)
    http_status: Optional[int] = Field(None, description="HTTP status code", example=200, ge=100, le=599)
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "source_url": "https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html",
                "title": "Sapiens: A Brief History of Humankind",
                "description": "A fascinating exploration of human history...",
                "category": "History",
                "price_incl_tax": 54.23,
                "price_excl_tax": 54.23,
                "availability": "In stock (20 available)",
                "num_reviews": 0,
                "image_url": "https://books.toscrape.com/media/cache/be/a5/bea5697f2534a2f86a3ef27b5a8c12a6.jpg",
                "rating": 5,
                "crawl_timestamp": "2025-11-09T20:00:00Z",
                "status": "success",
                "response_time": 0.523,
                "http_status": 200
            }
        }
    }


class BookListResponse(BaseModel):
    """
    Paginated list of books with metadata.
    
    Attributes:
        data: List of books on current page
        pagination: Pagination metadata
        filters_applied: Summary of applied filters (optional)
    """
    data: List[BookResponse] = Field(..., description="List of books")
    pagination: PaginationMeta = Field(..., description="Pagination information")
    filters_applied: Optional[Dict[str, Any]] = Field(
        None,
        description="Summary of filters applied to the query",
        example={"category": "Fiction", "min_rating": 4}
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "_id": "507f1f77bcf86cd799439011",
                        "title": "Sapiens: A Brief History of Humankind",
                        "category": "History",
                        "price_incl_tax": 54.23,
                        "rating": 5
                    }
                ],
                "pagination": {
                    "total": 1000,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 50,
                    "has_next": True,
                    "has_prev": False
                },
                "filters_applied": {
                    "category": "History",
                    "min_rating": 4
                }
            }
        }
    }


# ==================== Change Models ====================

class ChangeResponse(BaseModel):
    """
    Change record response model for tracking book updates.
    
    Attributes:
        id: Change record ID
        book_id: ID of the book that changed
        timestamp: When the change was detected
        change_type: Type of change (price, availability, content, new)
        old_value: Previous value (if applicable)
        new_value: New value (if applicable)
        field_changed: Which field was changed
    """
    id: str = Field(..., alias="_id", description="Change record ID")
    book_id: str = Field(..., description="Book that was changed")
    timestamp: datetime = Field(..., description="When the change occurred")
    change_type: str = Field(
        ..., 
        description="Type of change",
        example="price"
    )
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Optional[Any] = Field(None, description="New value")
    field_changed: Optional[str] = Field(None, description="Field that changed", example="price_incl_tax")
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f191e810c19729de860ea",
                "book_id": "507f1f77bcf86cd799439011",
                "timestamp": "2025-11-09T20:00:00Z",
                "change_type": "price",
                "old_value": 54.23,
                "new_value": 49.99,
                "field_changed": "price_incl_tax"
            }
        }
    }


class ChangeListResponse(BaseModel):
    """
    Paginated list of change records.
    
    Attributes:
        data: List of change records
        pagination: Pagination metadata
        since: Timestamp filter applied (if any)
    """
    data: List[ChangeResponse] = Field(..., description="List of changes")
    pagination: PaginationMeta = Field(..., description="Pagination information")
    since: Optional[datetime] = Field(
        None,
        description="Changes since this timestamp"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "_id": "507f191e810c19729de860ea",
                        "book_id": "507f1f77bcf86cd799439011",
                        "timestamp": "2025-11-09T20:00:00Z",
                        "change_type": "price",
                        "old_value": 54.23,
                        "new_value": 49.99,
                        "field_changed": "price_incl_tax"
                    }
                ],
                "pagination": {
                    "total": 150,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 8,
                    "has_next": True,
                    "has_prev": False
                },
                "since": "2025-11-08T00:00:00Z"
            }
        }
    }


# ==================== Health Response ====================

class HealthResponse(BaseModel):
    """
    Health check response model.
    
    Attributes:
        status: Overall health status
        service: Service name
        version: API version
        database: Database connection status
    """
    status: str = Field(..., description="Overall health status", example="healthy")
    service: str = Field(..., description="Service name", example="Books to Scrape API")
    version: str = Field(..., description="API version", example="1.0.0")
    database: Dict[str, Any] = Field(..., description="Database status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "service": "Books to Scrape API",
                "version": "1.0.0",
                "database": {
                    "status": "connected",
                    "database": "books",
                    "collections": 6,
                    "books_count": 1000
                }
            }
        }
    }
