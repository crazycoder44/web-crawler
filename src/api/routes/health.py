"""
Health Check Endpoint

Provides API health status and database connectivity check.
"""

from fastapi import APIRouter, status
from src.utils.database import check_database_health
from src.api.settings import settings
from src.api.models.schemas import HealthResponse
import logging

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="",
    tags=["Health"]
)


@router.get(
    "/health", 
    summary="Health check", 
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
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
        }
    }
)
async def health_check() -> HealthResponse:
    """
    Check API health and database connectivity.
    
    Returns:
        dict: Health status information including:
            - status: overall API health
            - service: API name
            - version: API version
            - database: database connection status and statistics
    
    Example response:
        {
            "status": "healthy",
            "service": "Books to Scrape API",
            "version": "1.0.0",
            "database": {
                "status": "connected",
                "database": "books_db",
                "collections": 2,
                "books_count": 1000
            }
        }
    """
    # Check database health
    db_health = await check_database_health()
    
    # Determine overall status
    overall_status = "healthy" if db_health.get("status") == "connected" else "degraded"
    
    return {
        "status": overall_status,
        "service": settings.api_title,
        "version": settings.api_version,
        "database": db_health
    }
