"""
Pagination Utilities

Helper functions for paginating query results.
Will be used in Steps 7-9.
"""

from typing import Any, List
from src.api.models.schemas import PaginationMeta
import math


def paginate(
    items: List[Any],
    total: int,
    page: int,
    limit: int
) -> PaginationMeta:
    """
    Generate pagination metadata.
    
    Args:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        limit: Maximum items per page
        
    Returns:
        PaginationMeta: Pagination metadata object
    """
    pages = math.ceil(total / limit) if limit > 0 else 0
    
    return PaginationMeta(
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )
