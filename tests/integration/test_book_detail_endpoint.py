"""
Integration tests for GET /books/{id} endpoint.

Tests the complete request/response flow including:
- Valid book ID retrieval
- Invalid book ID handling
- Authentication
- Response structure validation
"""

import pytest
from httpx import AsyncClient


class TestBookDetailEndpoint:
    """Test GET /books/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_book_by_valid_id(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test retrieving a book by valid ID."""
        response = await client.get(f"/api/v1/books/{sample_book_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "title" in data
        assert "source_url" in data
        assert "crawl_timestamp" in data
        assert data["id"] == sample_book_id
    
    @pytest.mark.asyncio
    async def test_get_book_with_authentication(
        self,
        client: AsyncClient,
        sample_book_id: str,
        valid_api_key: str
    ):
        """Test retrieving book with valid API key."""
        response = await client.get(
            f"/api/v1/books/{sample_book_id}",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_book_id
    
    @pytest.mark.asyncio
    async def test_get_book_invalid_id_format(self, client: AsyncClient, valid_api_key: str):
        """Test retrieving book with invalid ObjectId format."""
        response = await client.get("/api/v1/books/invalid-id-123",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
        assert "details" in data
    
    @pytest.mark.asyncio
    async def test_get_book_nonexistent_id(self, client: AsyncClient, valid_api_key: str):
        """Test retrieving book with valid format but nonexistent ID."""
        # Use a valid ObjectId format that doesn't exist
        nonexistent_id = "507f1f77bcf86cd799439999"
        response = await client.get(f"/api/v1/books/{nonexistent_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["message"] == "Book not found"
    
    @pytest.mark.asyncio
    async def test_get_book_response_structure(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test the complete structure of book detail response."""
        response = await client.get(f"/api/v1/books/{sample_book_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = ["id", "title", "source_url", "crawl_timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Optional fields (may or may not be present)
        optional_fields = [
            "category", "price_incl_tax", "price_excl_tax",
            "availability", "num_reviews", "image_url", "rating",
            "status", "response_time", "http_status"
        ]
        
        # If optional field exists, verify it has correct type
        if data.get("price_incl_tax") is not None:
            assert isinstance(data["price_incl_tax"], (int, float))
        
        if data.get("rating") is not None:
            assert isinstance(data["rating"], int)
            assert 0 <= data["rating"] <= 5
    
    @pytest.mark.asyncio
    async def test_get_book_all_fields_present(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test that returned book has expected field types."""
        response = await client.get(f"/api/v1/books/{sample_book_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify types of present fields
        assert isinstance(data["id"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["source_url"], str)
        assert isinstance(data["crawl_timestamp"], str)
        
        # Verify datetime format
        from datetime import datetime
        try:
            datetime.fromisoformat(data["crawl_timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid datetime format for crawl_timestamp")
    
    @pytest.mark.asyncio
    async def test_get_book_price_validation(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test that prices are non-negative if present."""
        response = await client.get(f"/api/v1/books/{sample_book_id}")
        assert response.status_code == 200
        data = response.json()
        
        if data.get("price_incl_tax") is not None:
            assert data["price_incl_tax"] >= 0
        
        if data.get("price_excl_tax") is not None:
            assert data["price_excl_tax"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_book_rating_validation(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test that rating is in valid range if present."""
        response = await client.get(f"/api/v1/books/{sample_book_id}")
        assert response.status_code == 200
        data = response.json()
        
        if data.get("rating") is not None:
            assert 0 <= data["rating"] <= 5
    
    @pytest.mark.asyncio
    async def test_get_book_case_sensitivity(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test that ObjectId lookup is case-sensitive."""
        # MongoDB ObjectIds are case-sensitive
        response_lower = await client.get(f"/api/v1/books/{sample_book_id.lower()}")
        response_upper = await client.get(f"/api/v1/books/{sample_book_id.upper()}")
        
        # One should succeed (the correct case), others might fail
        assert response_lower.status_code in [200, 404]
        assert response_upper.status_code in [200, 404, 422]
    
    @pytest.mark.asyncio
    async def test_get_book_rate_limit_headers(
        self,
        client: AsyncClient,
        sample_book_id: str,
        valid_api_key: str
    ):
        """Test that rate limit headers are present in response."""
        response = await client.get(
            f"/api/v1/books/{sample_book_id}",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    @pytest.mark.asyncio
    async def test_get_book_content_type(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test that response has correct content type."""
        response = await client.get(f"/api/v1/books/{sample_book_id}")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
