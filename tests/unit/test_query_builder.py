"""
Unit Tests for Query Builder Utility

Tests MongoDB query construction, validation, and helper functions.
"""
import pytest
from datetime import datetime
from bson import ObjectId
from src.api.utils.query_builder import (
    QueryBuilder,
    build_books_query,
    build_changes_query,
    build_sort_order,
    sanitize_query_value
)


class TestQueryBuilder:
    """Test QueryBuilder class methods."""
    
    def test_empty_query(self):
        """Test building empty query."""
        builder = QueryBuilder()
        query = builder.build()
        
        assert query == {}
    
    def test_add_exact_match(self):
        """Test adding exact match filter."""
        builder = QueryBuilder()
        query = builder.add_exact_match("category", "Fiction").build()
        
        assert query == {"category": "Fiction"}
    
    def test_add_exact_match_none_value(self):
        """Test exact match with None value (should skip)."""
        builder = QueryBuilder()
        query = builder.add_exact_match("category", None).build()
        
        assert query == {}
    
    def test_add_range_filter_both_bounds(self):
        """Test range filter with min and max."""
        builder = QueryBuilder()
        query = builder.add_range_filter("price", min_value=10.0, max_value=50.0).build()
        
        assert query == {"price": {"$gte": 10.0, "$lte": 50.0}}
    
    def test_add_range_filter_min_only(self):
        """Test range filter with min only."""
        builder = QueryBuilder()
        query = builder.add_range_filter("price", min_value=10.0).build()
        
        assert query == {"price": {"$gte": 10.0}}
    
    def test_add_range_filter_max_only(self):
        """Test range filter with max only."""
        builder = QueryBuilder()
        query = builder.add_range_filter("price", max_value=50.0).build()
        
        assert query == {"price": {"$lte": 50.0}}
    
    def test_add_range_filter_no_bounds(self):
        """Test range filter with no bounds (should skip)."""
        builder = QueryBuilder()
        query = builder.add_range_filter("price").build()
        
        assert query == {}
    
    def test_add_text_search(self):
        """Test adding text search filter."""
        builder = QueryBuilder()
        query = builder.add_text_search(["title", "description"], "python").build()
        
        assert "$or" in query
        assert len(query["$or"]) == 2
        assert query["$or"][0] == {"title": {"$regex": "python", "$options": "i"}}
    
    def test_add_text_search_empty_term(self):
        """Test text search with empty term (should skip)."""
        builder = QueryBuilder()
        query = builder.add_text_search(["title"], "").build()
        
        assert query == {}
    
    def test_add_contains_filter(self):
        """Test adding contains filter."""
        builder = QueryBuilder()
        query = builder.add_contains_filter("availability", "available").build()
        
        assert query == {"availability": {"$regex": "available", "$options": "i"}}
    
    def test_add_in_filter(self):
        """Test adding in filter."""
        builder = QueryBuilder()
        query = builder.add_in_filter("category", ["Fiction", "Travel"]).build()
        
        assert query == {"category": {"$in": ["Fiction", "Travel"]}}
    
    def test_add_in_filter_empty_list(self):
        """Test in filter with empty list (should skip)."""
        builder = QueryBuilder()
        query = builder.add_in_filter("category", []).build()
        
        assert query == {}
    
    def test_add_exists_filter(self):
        """Test adding exists filter."""
        builder = QueryBuilder()
        query = builder.add_exists_filter("description", True).build()
        
        assert query == {"description": {"$exists": True}}
    
    def test_add_comparison_filter(self):
        """Test adding comparison filter."""
        builder = QueryBuilder()
        query = builder.add_comparison_filter("rating", "$gte", 4).build()
        
        assert query == {"rating": {"$gte": 4}}
    
    def test_add_objectid_filter_valid(self):
        """Test adding ObjectId filter with valid ID."""
        builder = QueryBuilder()
        test_id = "507f1f77bcf86cd799439011"
        query = builder.add_objectid_filter("_id", test_id).build()
        
        assert "_id" in query
        assert isinstance(query["_id"], ObjectId)
        assert str(query["_id"]) == test_id
    
    def test_add_objectid_filter_invalid(self):
        """Test adding ObjectId filter with invalid ID."""
        builder = QueryBuilder()
        
        with pytest.raises(ValueError) as exc_info:
            builder.add_objectid_filter("_id", "invalid_id")
        
        assert "Invalid ObjectId format" in str(exc_info.value)
    
    def test_add_datetime_filter_after(self):
        """Test datetime filter with after date."""
        builder = QueryBuilder()
        test_date = datetime(2025, 11, 1)
        query = builder.add_datetime_filter("timestamp", after=test_date).build()
        
        assert query == {"timestamp": {"$gte": test_date}}
    
    def test_add_datetime_filter_before(self):
        """Test datetime filter with before date."""
        builder = QueryBuilder()
        test_date = datetime(2025, 11, 30)
        query = builder.add_datetime_filter("timestamp", before=test_date).build()
        
        assert query == {"timestamp": {"$lte": test_date}}
    
    def test_add_datetime_filter_both(self):
        """Test datetime filter with both after and before."""
        builder = QueryBuilder()
        after_date = datetime(2025, 11, 1)
        before_date = datetime(2025, 11, 30)
        query = builder.add_datetime_filter("timestamp", after=after_date, before=before_date).build()
        
        assert query == {"timestamp": {"$gte": after_date, "$lte": before_date}}
    
    def test_method_chaining(self):
        """Test method chaining."""
        builder = QueryBuilder()
        query = (builder
                 .add_exact_match("category", "Fiction")
                 .add_range_filter("price", min_value=10.0)
                 .add_comparison_filter("rating", "$gte", 4)
                 .build())
        
        assert "category" in query
        assert "price" in query
        assert "rating" in query
        assert query["category"] == "Fiction"
    
    def test_reset(self):
        """Test resetting query builder."""
        builder = QueryBuilder()
        builder.add_exact_match("category", "Fiction")
        builder.reset()
        query = builder.build()
        
        assert query == {}
    
    def test_multiple_filters_same_field(self):
        """Test adding multiple filters for same field."""
        builder = QueryBuilder()
        query = (builder
                 .add_range_filter("price", min_value=10.0, max_value=50.0)
                 .build())
        
        assert query["price"]["$gte"] == 10.0
        assert query["price"]["$lte"] == 50.0


class TestBuildBooksQuery:
    """Test build_books_query convenience function."""
    
    def test_empty_query(self):
        """Test building query with no parameters."""
        query = build_books_query()
        
        assert query == {}
    
    def test_category_filter(self):
        """Test building query with category."""
        query = build_books_query(category="Fiction")
        
        assert query["category"] == "Fiction"
    
    def test_price_range(self):
        """Test building query with price range."""
        query = build_books_query(min_price=10.0, max_price=50.0)
        
        assert query["price_incl_tax"]["$gte"] == 10.0
        assert query["price_incl_tax"]["$lte"] == 50.0
    
    def test_rating_filter(self):
        """Test building query with rating."""
        query = build_books_query(rating=4)
        
        assert query["rating"]["$gte"] == 4
    
    def test_availability_filter(self):
        """Test building query with availability."""
        query = build_books_query(availability="available")
        
        assert "availability" in query
        assert "$regex" in query["availability"]
    
    def test_search_filter(self):
        """Test building query with search term."""
        query = build_books_query(search="python")
        
        assert "$or" in query
        assert len(query["$or"]) == 2  # title and description
    
    def test_combined_filters(self):
        """Test building query with multiple filters."""
        query = build_books_query(
            category="Fiction",
            min_price=10.0,
            max_price=50.0,
            rating=4,
            availability="available",
            search="python"
        )
        
        assert "category" in query
        assert "price_incl_tax" in query
        assert "rating" in query
        assert "availability" in query
        assert "$or" in query


class TestBuildChangesQuery:
    """Test build_changes_query convenience function."""
    
    def test_empty_query(self):
        """Test building query with no parameters."""
        query = build_changes_query()
        
        assert query == {}
    
    def test_since_filter(self):
        """Test building query with since date."""
        test_date = datetime(2025, 11, 1)
        query = build_changes_query(since=test_date)
        
        assert query["timestamp"]["$gte"] == test_date
    
    def test_book_id_filter(self):
        """Test building query with book_id."""
        test_id = "507f1f77bcf86cd799439011"
        query = build_changes_query(book_id=test_id)
        
        assert "book_id" in query
        assert isinstance(query["book_id"], ObjectId)
    
    def test_change_type_filter(self):
        """Test building query with change_type."""
        query = build_changes_query(change_type="update")
        
        assert query["change_type"] == "update"
    
    def test_combined_filters(self):
        """Test building query with multiple filters."""
        test_date = datetime(2025, 11, 1)
        test_id = "507f1f77bcf86cd799439011"
        query = build_changes_query(
            since=test_date,
            book_id=test_id,
            change_type="update"
        )
        
        assert "timestamp" in query
        assert "book_id" in query
        assert "change_type" in query


class TestBuildSortOrder:
    """Test build_sort_order function."""
    
    def test_sort_by_title(self):
        """Test sorting by title."""
        sort = build_sort_order("title")
        
        assert sort == [("title", 1)]
    
    def test_sort_by_price_asc(self):
        """Test sorting by price ascending."""
        sort = build_sort_order("price_asc")
        
        assert sort == [("price_incl_tax", 1)]
    
    def test_sort_by_price_desc(self):
        """Test sorting by price descending."""
        sort = build_sort_order("price_desc")
        
        assert sort == [("price_incl_tax", -1)]
    
    def test_sort_by_rating_asc(self):
        """Test sorting by rating ascending."""
        sort = build_sort_order("rating_asc")
        
        assert sort == [("rating", 1)]
    
    def test_sort_by_rating_desc(self):
        """Test sorting by rating descending."""
        sort = build_sort_order("rating_desc")
        
        assert sort == [("rating", -1)]
    
    def test_sort_by_recent(self):
        """Test sorting by recent (timestamp)."""
        sort = build_sort_order("recent")
        
        assert sort == [("crawl_timestamp", -1)]
    
    def test_invalid_sort(self):
        """Test invalid sort option returns default."""
        sort = build_sort_order("invalid_sort")
        
        assert sort == [("_id", -1)]
    
    def test_custom_default_sort(self):
        """Test custom default sort."""
        sort = build_sort_order("invalid", default_sort=[("custom_field", 1)])
        
        assert sort == [("custom_field", 1)]


class TestSanitizeQueryValue:
    """Test sanitize_query_value function."""
    
    def test_sanitize_int(self):
        """Test sanitizing string to int."""
        result = sanitize_query_value("123", int)
        
        assert result == 123
        assert isinstance(result, int)
    
    def test_sanitize_float(self):
        """Test sanitizing string to float."""
        result = sanitize_query_value("123.45", float)
        
        assert result == 123.45
        assert isinstance(result, float)
    
    def test_sanitize_bool_true(self):
        """Test sanitizing string to bool (true)."""
        assert sanitize_query_value("true", bool) is True
        assert sanitize_query_value("True", bool) is True
        assert sanitize_query_value("1", bool) is True
        assert sanitize_query_value("yes", bool) is True
    
    def test_sanitize_bool_false(self):
        """Test sanitizing string to bool (false)."""
        assert sanitize_query_value("false", bool) is False
        assert sanitize_query_value("False", bool) is False
        assert sanitize_query_value("0", bool) is False
        assert sanitize_query_value("no", bool) is False
    
    def test_sanitize_string(self):
        """Test sanitizing string (strips whitespace)."""
        result = sanitize_query_value("  test  ", str)
        
        assert result == "test"
    
    def test_sanitize_invalid_int(self):
        """Test sanitizing invalid int raises error."""
        with pytest.raises(ValueError):
            sanitize_query_value("not_a_number", int)
    
    def test_sanitize_invalid_float(self):
        """Test sanitizing invalid float raises error."""
        with pytest.raises(ValueError):
            sanitize_query_value("not_a_float", float)
    
    def test_sanitize_already_correct_type(self):
        """Test sanitizing value that's already correct type."""
        result = sanitize_query_value(123, int)
        
        assert result == 123


class TestQueryBuilderEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_string_values(self):
        """Test that empty strings in exact match are kept, but ignored in contains filter."""
        builder = QueryBuilder()
        query = (builder
                 .add_exact_match("field1", "")
                 .add_contains_filter("field2", "")
                 .build())
        
        # Empty string in exact match is valid, but contains filter ignores it
        assert query == {"field1": ""}
    
    def test_none_values_ignored(self):
        """Test that None values are ignored."""
        builder = QueryBuilder()
        query = (builder
                 .add_exact_match("field1", None)
                 .add_range_filter("field2", min_value=None, max_value=None)
                 .build())
        
        assert query == {}
    
    def test_special_characters_in_regex(self):
        """Test special regex characters are handled."""
        builder = QueryBuilder()
        query = builder.add_contains_filter("field", "test*value").build()
        
        # Should still create a valid regex
        assert "field" in query
        assert "$regex" in query["field"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
