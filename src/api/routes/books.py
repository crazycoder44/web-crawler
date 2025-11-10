"""
Books API Routes

Handles all book-related endpoints:
- GET /books - List books with filtering and pagination
- GET /books/{book_id} - Get single book details
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from typing import Optional, List
from datetime import datetime
import logging

from src.utils.database import get_database
from src.api.dependencies import require_api_key
from src.api.models.schemas import BookListResponse, BookResponse, PaginationMeta, ErrorResponse
from bson import ObjectId
from src.api.settings import settings

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/books",
    tags=["Books"],
    responses={
        401: {"description": "Unauthorized - Invalid API key"},
        429: {"description": "Too Many Requests - Rate limit exceeded"}
    }
)


@router.get(
    "",
    response_model=BookListResponse,
    summary="List all books",
    description="Retrieve a paginated list of books with optional filtering and sorting",
    responses={
        200: {
            "description": "Successful response with paginated book list",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": "507f1f77bcf86cd799439011",
                                "title": "A Light in the Attic",
                                "category": "Poetry",
                                "price_incl_tax": 51.77,
                                "price_excl_tax": 51.77,
                                "availability": "In stock (22 available)",
                                "rating": 3,
                                "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                                "crawl_timestamp": "2025-11-10T12:00:00Z"
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
                            "category": "Poetry",
                            "min_price": 10.0,
                            "max_price": 100.0
                        }
                    }
                }
            }
        },
        401: {
            "description": "Missing or invalid API key",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Missing API key",
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        },
        422: {
            "description": "Validation error (invalid parameters)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Validation error",
                        "details": {
                            "page": "must be >= 1",
                            "rating": "must be between 1 and 5"
                        },
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Rate limit exceeded. Try again later.",
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        }
    }
)
async def list_books(
    # Filtering parameters
    category: Optional[str] = Query(
        None,
        description="Filter by book category (e.g., Travel, Fiction, Mystery)",
        example="Travel"
    ),
    min_price: Optional[float] = Query(
        None,
        ge=0,
        description="Minimum price filter (inclusive)",
        example=10.0
    ),
    max_price: Optional[float] = Query(
        None,
        ge=0,
        description="Maximum price filter (inclusive)",
        example=50.0
    ),
    rating: Optional[int] = Query(
        None,
        ge=1,
        le=5,
        description="Filter by minimum rating (1-5 stars)",
        example=4
    ),
    availability: Optional[str] = Query(
        None,
        description="Filter by availability status (e.g., 'In stock', or check for 'available')",
        example="available"
    ),
    search: Optional[str] = Query(
        None,
        description="Search in book title and description",
        example="travel"
    ),
    # Sorting parameters
    sort_by: str = Query(
        "recent",
        description="Sort order: 'recent' (newest first), 'title' (A-Z), 'price_asc', 'price_desc', 'rating_desc'",
        regex="^(recent|title|price_asc|price_desc|rating_desc)$"
    ),
    # Pagination parameters
    page: int = Query(
        1,
        ge=1,
        description="Page number (starts at 1)"
    ),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Items per page (max: {settings.max_page_size})"
    ),
    # Authentication
    api_key: str = Depends(require_api_key)
):
    """
    Retrieve a paginated list of books with powerful filtering and sorting options.
    
    **Authentication Required**: Include `X-API-Key` header with valid API key.
    
    **Filtering Options:**
    - `category`: Filter by book category (exact match, case-sensitive)
    - `min_price` / `max_price`: Filter by price range
    - `rating`: Filter by minimum rating (1-5)
    - `availability`: Filter by availability (checks if text contains the query)
    - `search`: Search in title and description (case-insensitive)
    
    **Sorting Options:**
    - `recent`: Newest books first (by crawl timestamp)
    - `title`: Alphabetical by title (A-Z)
    - `price_asc`: Lowest price first
    - `price_desc`: Highest price first
    - `rating_desc`: Highest rating first
    
    **Pagination:**
    - `page`: Page number (starts at 1)
    - `limit`: Items per page (default: 20, max: 100)
    
    **Response:**
    Returns a paginated list with metadata including total count and page information.
    """
    try:
        db = get_database()
        collection = db["books"]
        
        # Build query filters
        query = {}
        
        # Category filter (exact match)
        if category:
            query["category"] = category
        
        # Price range filter
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            query["price_incl_tax"] = price_filter
        
        # Rating filter (minimum rating)
        if rating is not None:
            query["rating"] = {"$gte": rating}
        
        # Availability filter (contains text)
        if availability:
            query["availability"] = {"$regex": availability, "$options": "i"}
        
        # Search filter (in title and description)
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Build sort order
        sort_order = []
        if sort_by == "recent":
            sort_order = [("crawl_timestamp", -1)]
        elif sort_by == "title":
            sort_order = [("title", 1)]
        elif sort_by == "price_asc":
            sort_order = [("price_incl_tax", 1)]
        elif sort_by == "price_desc":
            sort_order = [("price_incl_tax", -1)]
        elif sort_by == "rating_desc":
            sort_order = [("rating", -1)]
        
        # Get total count for pagination
        total_count = await collection.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        # Execute query with pagination
        cursor = collection.find(query).sort(sort_order).skip(skip).limit(limit)
        books = await cursor.to_list(length=limit)
        
        # Convert MongoDB documents to response models
        book_responses = []
        for book in books:
            book_responses.append(BookResponse(
                id=str(book["_id"]),
                title=book.get("title", ""),
                description=book.get("description"),
                category=book.get("category"),
                price=book.get("price_incl_tax"),
                availability=book.get("availability"),
                rating=book.get("rating"),
                num_reviews=book.get("num_reviews", 0),
                image_url=book.get("image_url"),
                source_url=book.get("source_url"),
                crawl_timestamp=book.get("crawl_timestamp")
            ))
        
        # Build pagination metadata
        pagination = PaginationMeta(
            total=total_count,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        logger.info(
            f"Books list request: filters={query}, sort={sort_by}, "
            f"page={page}, total={total_count}, api_key={api_key[:8]}..."
        )
        
        return BookListResponse(
            data=book_responses,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error fetching books: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch books: {str(e)}"
        )


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get book by ID",
    description="Retrieve detailed information about a specific book by its MongoDB ObjectId",
    responses={
        200: {
            "description": "Book found and returned successfully",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        },
        401: {
            "description": "Missing or invalid API key",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Missing API key",
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Book not found",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Book with ID '507f1f77bcf86cd799439011' not found",
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        },
        422: {
            "description": "Invalid book ID format (must be 24-character hex string)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Invalid book ID format: 'invalid-id'. Must be a valid MongoDB ObjectId.",
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        }
    }
)
async def get_book(
    book_id: str = Path(
        ...,
        description="MongoDB ObjectId of the book (24-character hexadecimal string)",
        example="507f1f77bcf86cd799439011"
    ),
    api_key: str = Depends(require_api_key)
):
    """
    Retrieve detailed information about a specific book.
    
    This endpoint returns complete book data including:
    - Basic info (title, category, description)
    - Pricing (price_incl_tax, price_excl_tax)
    - Availability and stock status
    - Rating and reviews
    - Crawl metadata (timestamp, response time, status)
    - Image URL and source URL
    
    **Authentication Required**: Include `X-API-Key` header
    
    **Path Parameters:**
    - `book_id`: MongoDB ObjectId (24-character hex string)
    
    **Example Request:**
    ```
    GET /books/507f1f77bcf86cd799439011
    X-API-Key: your_api_key_here
    ```
    
    **Returns:**
    - `200 OK`: Book details
    - `401 Unauthorized`: Invalid/missing API key
    - `404 Not Found`: Book doesn't exist
    - `422 Unprocessable Entity`: Invalid ObjectId format
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            logger.warning(f"Invalid ObjectId format: {book_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid book ID format. Expected 24-character hexadecimal string, got: {book_id}"
            )
        
        # Convert string to ObjectId
        obj_id = ObjectId(book_id)
        
        # Query database (Motor is async)
        db = get_database()
        book = await db.books.find_one({"_id": obj_id})
        
        if not book:
            logger.info(f"Book not found: {book_id}, api_key={api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with ID '{book_id}' not found"
            )
        
        # Convert ObjectId to string for response
        book["_id"] = str(book["_id"])
        
        # Build response
        book_response = BookResponse(
            id=book["_id"],
            title=book.get("title", "Unknown"),
            description=book.get("description"),
            category=book.get("category"),
            price_incl_tax=book.get("price_incl_tax"),
            price_excl_tax=book.get("price_excl_tax"),
            availability=book.get("availability"),
            rating=book.get("rating"),
            num_reviews=book.get("num_reviews", 0),
            image_url=book.get("image_url"),
            source_url=book.get("source_url"),
            crawl_timestamp=book.get("crawl_timestamp"),
            raw_html_hash=book.get("raw_html_hash"),
            raw_html_snapshot_path=book.get("raw_html_snapshot_path"),
            status=book.get("status"),
            response_time=book.get("response_time"),
            http_status=book.get("http_status")
        )
        
        logger.info(f"Book retrieved: {book_id}, title='{book.get('title', 'Unknown')[:50]}...', api_key={api_key[:8]}...")
        
        return book_response
        
    except HTTPException:
        # Re-raise HTTP exceptions (404, 422)
        raise
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch book: {str(e)}"
        )
