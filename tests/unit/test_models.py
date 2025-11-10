"""
Unit Tests for Pydantic Models/Schemas

Tests validation, serialization, and field requirements.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from src.api.models.schemas import (
    BookResponse,
    BookListResponse,
    ChangeResponse,
    ChangeListResponse,
    ErrorResponse,
    PaginationMeta
)


class TestBookResponse:
    """Test BookResponse model."""
    
    def test_valid_book_response(self, sample_book_data):
        """Test creating valid book response."""
        book = BookResponse(**sample_book_data)
        
        assert book.title == "Test Book"
        assert book.price_incl_tax == 24.60
        assert book.rating == 4
        assert book.category == "Fiction"
    
    def test_book_response_without_optional_fields(self):
        """Test book response without optional fields."""
        minimal_data = {
            "_id": "507f1f77bcf86cd799439011",
            "source_url": "http://example.com",
            "title": "Minimal Book",
            "crawl_timestamp": "2025-11-10T00:00:00"
        }
        
        book = BookResponse(**minimal_data)
        assert book.description is None
        assert book.status is None
    
    def test_book_response_price_validation(self):
        """Test price must be non-negative."""
        data = {
            "_id": "507f1f77bcf86cd799439011",
            "source_url": "http://example.com",
            "title": "Test",
            "price_excl_tax": -10.0,  # Invalid
            "price_incl_tax": 12.0,
            "crawl_timestamp": "2025-11-10T00:00:00"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BookResponse(**data)
        
        assert "price_excl_tax" in str(exc_info.value)
    
    def test_book_response_rating_validation(self):
        """Test rating must be between 0 and 5."""
        data = {
            "_id": "507f1f77bcf86cd799439011",
            "source_url": "http://example.com",
            "title": "Test",
            "rating": 6,  # Invalid
            "crawl_timestamp": "2025-11-10T00:00:00"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BookResponse(**data)
        
        assert "rating" in str(exc_info.value)
    
    def test_book_response_serialization(self, sample_book_data):
        """Test book response can be serialized to dict."""
        book = BookResponse(**sample_book_data)
        data = book.model_dump()
        
        assert isinstance(data, dict)
        assert data["title"] == "Test Book"
        assert data["price_incl_tax"] == 24.60


class TestPaginationMeta:
    """Test PaginationMeta model."""
    
    def test_valid_pagination(self, sample_pagination_data):
        """Test creating valid pagination metadata."""
        pagination = PaginationMeta(**sample_pagination_data)
        
        assert pagination.page == 1
        assert pagination.page_size == 20
        assert pagination.total == 100
        assert pagination.total_pages == 5
    
    def test_pagination_validation(self):
        """Test pagination field validation."""
        # Page must be >= 1
        with pytest.raises(ValidationError):
            PaginationMeta(total=100, page=0, page_size=20, total_pages=5, has_next=True, has_prev=False)
        
        # Page size must be >= 1
        with pytest.raises(ValidationError):
            PaginationMeta(total=100, page=1, page_size=0, total_pages=5, has_next=True, has_prev=False)
        
        # Total must be >= 0
        with pytest.raises(ValidationError):
            PaginationMeta(total=-1, page=1, page_size=20, total_pages=5, has_next=True, has_prev=False)


class TestBookListResponse:
    """Test BookListResponse model."""
    
    def test_valid_book_list_response(self, sample_book_data, sample_pagination_data):
        """Test creating valid book list response."""
        response = BookListResponse(
            data=[BookResponse(**sample_book_data)],
            pagination=PaginationMeta(**sample_pagination_data)
        )
        
        assert len(response.data) == 1
        assert response.data[0].title == "Test Book"
        assert response.pagination.page == 1
    
    def test_empty_book_list(self):
        """Test book list with no results."""
        response = BookListResponse(
            data=[],
            pagination=PaginationMeta(
                total=0,
                page=1,
                page_size=20,
                total_pages=0,
                has_next=False,
                has_prev=False
            )
        )
        
        assert len(response.data) == 0
        assert response.pagination.total == 0


class TestChangeResponse:
    """Test ChangeResponse model."""
    
    def test_valid_change_response(self, sample_change_data):
        """Test creating valid change response."""
        change = ChangeResponse(**sample_change_data)
        
        assert change.book_id == "507f1f77bcf86cd799439011"
        assert change.change_type == "update"
        assert change.field_changed == "price_incl_tax"
        assert change.old_value == 24.60
        assert change.new_value == 22.40
    
    def test_change_response_without_optional_fields(self):
        """Test change response without optional fields."""
        minimal_data = {
            "_id": "507f1f77bcf86cd799439012",
            "book_id": "507f1f77bcf86cd799439011",
            "timestamp": "2025-11-10T01:00:00",
            "change_type": "create"
        }
        
        change = ChangeResponse(**minimal_data)
        assert change.field_changed is None
        assert change.old_value is None
        assert change.new_value is None


class TestChangeListResponse:
    """Test ChangeListResponse model."""
    
    def test_valid_change_list_response(self, sample_change_data, sample_pagination_data):
        """Test creating valid change list response."""
        response = ChangeListResponse(
            data=[ChangeResponse(**sample_change_data)],
            pagination=PaginationMeta(**sample_pagination_data)
        )
        
        assert len(response.data) == 1
        assert response.data[0].change_type == "update"
        assert response.pagination.total == 100


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_valid_error_response(self):
        """Test creating valid error response."""
        error = ErrorResponse(
            status="error",
            message="Invalid input",
            timestamp="2025-11-10T00:00:00"
        )
        
        assert error.status == "error"
        assert error.message == "Invalid input"
    
    def test_error_response_with_details(self):
        """Test error response with validation details."""
        error = ErrorResponse(
            status="error",
            message="Validation failed",
            timestamp="2025-11-10T00:00:00",
            details={"field": "price", "message": "Must be positive"}
        )
        
        assert error.details is not None
        assert error.details["field"] == "price"


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_book_json_serialization(self, sample_book_data):
        """Test book can be serialized to JSON."""
        book = BookResponse(**sample_book_data)
        json_str = book.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "Test Book" in json_str
    
    def test_book_json_deserialization(self, sample_book_data):
        """Test book can be deserialized from dict."""
        book = BookResponse(**sample_book_data)
        data = book.model_dump()
        
        # Create new instance from dict
        book2 = BookResponse(**{**sample_book_data, **data})
        assert book2.title == book.title
        assert book2.price_incl_tax == book.price_incl_tax
    
    def test_pagination_serialization(self, sample_pagination_data):
        """Test pagination can be serialized."""
        pagination = PaginationMeta(**sample_pagination_data)
        
        data = pagination.model_dump()
        assert data["page"] == 1
        assert data["page_size"] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
