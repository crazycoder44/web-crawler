"""
Changes API Routes

Handles change detection history endpoints:
- GET /changes - List change history with filtering
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from datetime import datetime
import logging

from src.utils.database import get_database
from src.api.dependencies import require_api_key
from src.api.models.schemas import ChangeListResponse, ChangeResponse, PaginationMeta, ErrorResponse
from bson import ObjectId

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/changes",
    tags=["Changes"],
    responses={
        401: {"description": "Unauthorized - Invalid API key"},
        429: {"description": "Too Many Requests - Rate limit exceeded"}
    }
)


@router.get(
    "",
    response_model=ChangeListResponse,
    summary="List book changes",
    description="Retrieve change history with filtering by time, book ID, and change type",
    responses={
        200: {
            "description": "List of changes returned successfully",
            "content": {
                "application/json": {
                    "example": {
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
                            "has_next": True,
                            "has_prev": False
                        },
                        "filters_applied": {
                            "since": "2025-11-08T00:00:00Z",
                            "change_type": "update"
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
            "description": "Invalid query parameters (e.g., invalid date format or book ID)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Validation error",
                        "details": {
                            "since": "Invalid datetime format. Use ISO 8601: YYYY-MM-DDTHH:MM:SSZ",
                            "book_id": "Invalid MongoDB ObjectId format"
                        },
                        "timestamp": "2025-11-10T12:00:00Z"
                    }
                }
            }
        }
    }
)
async def list_changes(
    since: Optional[datetime] = Query(
        None,
        description="Show changes since this timestamp (ISO 8601 format)",
        example="2025-11-08T00:00:00Z"
    ),
    book_id: Optional[str] = Query(
        None,
        description="Filter by specific book ID (MongoDB ObjectId)",
        example="507f1f77bcf86cd799439011"
    ),
    change_type: Optional[str] = Query(
        None,
        description="Filter by change type",
        example="update"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page (max 100)"
    ),
    api_key: str = Depends(require_api_key)
):
    """
    Retrieve change history for book catalog updates.
    
    This endpoint tracks all changes detected in the book catalog, including:
    - Price changes
    - Availability updates
    - Content modifications
    - New book additions
    
    **Authentication Required**: Include `X-API-Key` header
    
    **Query Parameters:**
    - `since` (optional): ISO 8601 timestamp - only show changes after this time
    - `book_id` (optional): MongoDB ObjectId - filter changes for specific book
    - `change_type` (optional): Filter by type (e.g., "update", "insert")
    - `page` (default: 1): Page number for pagination
    - `limit` (default: 20, max: 100): Number of changes per page
    
    **Example Requests:**
    ```
    # Get recent changes
    GET /changes?limit=10
    
    # Get changes since specific time
    GET /changes?since=2025-11-08T00:00:00Z
    
    # Get changes for specific book
    GET /changes?book_id=507f1f77bcf86cd799439011
    
    # Combine filters
    GET /changes?since=2025-11-08T00:00:00Z&change_type=update&page=2
    ```
    
    **Returns:**
    - `200 OK`: List of changes with pagination metadata
    - `401 Unauthorized`: Invalid/missing API key
    - `422 Unprocessable Entity`: Invalid query parameters
    """
    try:
        # Validate book_id if provided
        if book_id and not ObjectId.is_valid(book_id):
            logger.warning(f"Invalid book_id format: {book_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid book_id format. Expected 24-character hexadecimal string, got: {book_id}"
            )
        
        # Build query filter
        query = {}
        
        # Time-based filter
        if since:
            query["timestamp"] = {"$gte": since}
        
        # Book-specific filter
        if book_id:
            query["book_id"] = ObjectId(book_id)
        
        # Change type filter
        if change_type:
            query["change_type"] = change_type
        
        # Get database and collection
        db = get_database()
        collection = db.book_changes
        
        # Get total count for pagination
        total_count = await collection.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit
        
        # Execute query with pagination (sort by timestamp descending - newest first)
        cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        changes = await cursor.to_list(length=limit)
        
        # Build response objects
        change_responses = []
        for change in changes:
            # Convert ObjectIds to strings
            change_id = str(change["_id"])
            book_id_str = str(change["book_id"])
            
            # Extract change details from the 'changes' dict
            changes_dict = change.get("changes", {})
            
            # Determine primary field that changed and its values
            field_changed = None
            old_value = None
            new_value = None
            
            if changes_dict:
                # Get the first changed field as primary
                field_changed = list(changes_dict.keys())[0]
                field_data = changes_dict[field_changed]
                
                if isinstance(field_data, dict):
                    old_value = field_data.get("old")
                    new_value = field_data.get("new")
            
            change_responses.append(ChangeResponse(
                id=change_id,
                book_id=book_id_str,
                timestamp=change["timestamp"],
                change_type=change.get("change_type", "unknown"),
                field_changed=field_changed,
                old_value=old_value,
                new_value=new_value
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
            f"Changes list request: filters={query}, page={page}, total={total_count}, "
            f"api_key={api_key[:8]}..."
        )
        
        return ChangeListResponse(
            data=change_responses,
            pagination=pagination,
            since=since
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching changes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch changes: {str(e)}"
        )
