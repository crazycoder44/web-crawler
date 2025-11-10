"""
MongoDB Query Builder Utility

Provides type-safe, reusable functions for building MongoDB queries.
Supports filtering, range queries, text search, and complex conditions.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class QueryBuilder:
    """
    Builder class for constructing MongoDB queries with validation.
    
    Provides a fluent interface for building complex queries with multiple filters.
    """
    
    def __init__(self):
        self.query: Dict[str, Any] = {}
    
    def add_exact_match(self, field: str, value: Any) -> 'QueryBuilder':
        """
        Add an exact match filter.
        
        Args:
            field: Field name to filter on
            value: Value to match exactly
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_exact_match("category", "Travel")
        """
        if value is not None:
            self.query[field] = value
        return self
    
    def add_range_filter(
        self,
        field: str,
        min_value: Optional[Union[int, float, datetime]] = None,
        max_value: Optional[Union[int, float, datetime]] = None
    ) -> 'QueryBuilder':
        """
        Add a range filter (greater than/less than).
        
        Args:
            field: Field name to filter on
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_range_filter("price_incl_tax", min_value=10.0, max_value=50.0)
        """
        if min_value is not None or max_value is not None:
            range_query = {}
            if min_value is not None:
                range_query["$gte"] = min_value
            if max_value is not None:
                range_query["$lte"] = max_value
            
            if range_query:
                self.query[field] = range_query
        
        return self
    
    def add_text_search(
        self,
        fields: List[str],
        search_term: str,
        case_insensitive: bool = True
    ) -> 'QueryBuilder':
        """
        Add text search across multiple fields using regex.
        
        Args:
            fields: List of field names to search
            search_term: Search term
            case_insensitive: Whether search is case-insensitive
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_text_search(["title", "description"], "python")
        """
        if search_term:
            options = "i" if case_insensitive else ""
            self.query["$or"] = [
                {field: {"$regex": search_term, "$options": options}}
                for field in fields
            ]
        return self
    
    def add_contains_filter(
        self,
        field: str,
        value: str,
        case_insensitive: bool = True
    ) -> 'QueryBuilder':
        """
        Add a "contains" filter for partial string matching.
        
        Args:
            field: Field name to filter on
            value: Substring to search for
            case_insensitive: Whether search is case-insensitive
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_contains_filter("availability", "available")
        """
        if value:
            options = "i" if case_insensitive else ""
            self.query[field] = {"$regex": value, "$options": options}
        return self
    
    def add_in_filter(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """
        Add an "in" filter for matching any value in a list.
        
        Args:
            field: Field name to filter on
            values: List of values to match
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_in_filter("category", ["Fiction", "Travel", "History"])
        """
        if values:
            self.query[field] = {"$in": values}
        return self
    
    def add_exists_filter(self, field: str, exists: bool = True) -> 'QueryBuilder':
        """
        Add an existence check filter.
        
        Args:
            field: Field name to check
            exists: True to check field exists, False to check it doesn't
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_exists_filter("description", True)
        """
        self.query[field] = {"$exists": exists}
        return self
    
    def add_comparison_filter(
        self,
        field: str,
        operator: str,
        value: Any
    ) -> 'QueryBuilder':
        """
        Add a comparison filter with custom operator.
        
        Args:
            field: Field name to filter on
            operator: MongoDB operator ($gt, $lt, $gte, $lte, $ne, $eq)
            value: Value to compare against
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_comparison_filter("rating", "$gte", 4)
        """
        if value is not None:
            self.query[field] = {operator: value}
        return self
    
    def add_objectid_filter(self, field: str, object_id: str) -> 'QueryBuilder':
        """
        Add an ObjectId filter with validation.
        
        Args:
            field: Field name to filter on
            object_id: String representation of ObjectId
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If object_id is not a valid ObjectId format
            
        Example:
            builder.add_objectid_filter("book_id", "507f1f77bcf86cd799439011")
        """
        if object_id:
            if not ObjectId.is_valid(object_id):
                raise ValueError(f"Invalid ObjectId format: {object_id}")
            self.query[field] = ObjectId(object_id)
        return self
    
    def add_datetime_filter(
        self,
        field: str,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> 'QueryBuilder':
        """
        Add a datetime range filter.
        
        Args:
            field: Field name to filter on
            after: Filter for dates after this (inclusive)
            before: Filter for dates before this (inclusive)
            
        Returns:
            Self for method chaining
            
        Example:
            builder.add_datetime_filter("crawl_timestamp", after=datetime(2025, 11, 1))
        """
        return self.add_range_filter(field, min_value=after, max_value=before)
    
    def build(self) -> Dict[str, Any]:
        """
        Build and return the final query.
        
        Returns:
            MongoDB query dictionary
        """
        return self.query
    
    def reset(self) -> 'QueryBuilder':
        """
        Reset the query to empty state.
        
        Returns:
            Self for method chaining
        """
        self.query = {}
        return self


def build_books_query(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rating: Optional[int] = None,
    availability: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a query for filtering books.
    
    Convenience function that wraps QueryBuilder for common book filters.
    
    Args:
        category: Filter by category
        min_price: Minimum price (inclusive)
        max_price: Maximum price (inclusive)
        rating: Minimum rating
        availability: Filter by availability text
        search: Search in title and description
        
    Returns:
        MongoDB query dictionary
        
    Example:
        query = build_books_query(category="Fiction", min_price=10, rating=4)
    """
    builder = QueryBuilder()
    
    # Category filter
    if category:
        builder.add_exact_match("category", category)
    
    # Price range filter
    if min_price is not None or max_price is not None:
        builder.add_range_filter("price_incl_tax", min_value=min_price, max_value=max_price)
    
    # Rating filter (minimum rating)
    if rating is not None:
        builder.add_comparison_filter("rating", "$gte", rating)
    
    # Availability filter (contains text)
    if availability:
        builder.add_contains_filter("availability", availability)
    
    # Search filter (in title and description)
    if search:
        builder.add_text_search(["title", "description"], search)
    
    return builder.build()


def build_changes_query(
    since: Optional[datetime] = None,
    book_id: Optional[str] = None,
    change_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a query for filtering changes.
    
    Convenience function that wraps QueryBuilder for common change filters.
    
    Args:
        since: Filter changes after this timestamp
        book_id: Filter changes for specific book
        change_type: Filter by change type
        
    Returns:
        MongoDB query dictionary
        
    Raises:
        ValueError: If book_id is not a valid ObjectId format
        
    Example:
        query = build_changes_query(since=datetime(2025, 11, 1), change_type="update")
    """
    builder = QueryBuilder()
    
    # Time-based filter
    if since:
        builder.add_datetime_filter("timestamp", after=since)
    
    # Book-specific filter
    if book_id:
        builder.add_objectid_filter("book_id", book_id)
    
    # Change type filter
    if change_type:
        builder.add_exact_match("change_type", change_type)
    
    return builder.build()


def build_sort_order(sort_by: str, default_sort: List[tuple] = None) -> List[tuple]:
    """
    Build MongoDB sort order from sort parameter.
    
    Args:
        sort_by: Sort parameter (e.g., "title", "price_asc", "rating_desc")
        default_sort: Default sort order if sort_by is not recognized
        
    Returns:
        List of (field, direction) tuples for MongoDB sort
        
    Example:
        sort = build_sort_order("price_asc")  # Returns [("price_incl_tax", 1)]
    """
    if default_sort is None:
        default_sort = [("_id", -1)]
    
    sort_mapping = {
        "title": [("title", 1)],
        "price_asc": [("price_incl_tax", 1)],
        "price_desc": [("price_incl_tax", -1)],
        "rating_asc": [("rating", 1)],
        "rating_desc": [("rating", -1)],
        "recent": [("crawl_timestamp", -1)],
        "oldest": [("crawl_timestamp", 1)],
    }
    
    return sort_mapping.get(sort_by, default_sort)


def sanitize_query_value(value: Any, expected_type: type = str) -> Any:
    """
    Sanitize and validate query parameter values.
    
    Args:
        value: Value to sanitize
        expected_type: Expected type for the value
        
    Returns:
        Sanitized value
        
    Raises:
        ValueError: If value cannot be converted to expected type
    """
    if value is None:
        return None
    
    try:
        if expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        elif expected_type == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        elif expected_type == str:
            return str(value).strip()
        else:
            return value
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert '{value}' to {expected_type.__name__}: {e}")
        raise ValueError(f"Invalid value '{value}' for type {expected_type.__name__}")
