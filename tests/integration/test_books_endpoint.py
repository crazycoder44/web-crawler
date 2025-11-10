"""
Integration tests for GET /books endpoint.

Tests the complete request/response flow including:
- Pagination
- Filtering (category, price, rating, availability, search)
- Sorting
- Authentication
- Error handling
"""

import pytest
from httpx import AsyncClient


class TestBooksListEndpoint:
    """Test GET /books endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_books_without_auth(self, client: AsyncClient):
        """Test accessing books endpoint without authentication."""
        response = await client.get("/api/v1/books")
        assert response.status_code == 401  # Should require authentication
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_get_books_with_valid_auth(self, client: AsyncClient, valid_api_key: str):
        """Test accessing books with valid API key."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_get_books_pagination_default(self, client: AsyncClient, valid_api_key: str):
        """Test default pagination parameters."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 20
        assert pagination["total"] > 0
        assert "has_next" in pagination
        assert "has_prev" in pagination
        assert pagination["has_prev"] is False
    
    @pytest.mark.asyncio
    async def test_get_books_pagination_custom(self, client: AsyncClient, valid_api_key: str):
        """Test custom pagination parameters."""
        response = await client.get(
            "/api/v1/books?page=2&page_size=10",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        assert pagination["page"] == 2
        assert pagination["page_size"] == 10
        assert len(data["data"]) <= 10
    
    @pytest.mark.asyncio
    async def test_get_books_pagination_invalid_page(self, client: AsyncClient, valid_api_key: str):
        """Test invalid page number."""
        response = await client.get(
            "/api/v1/books?page=0",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_get_books_pagination_invalid_page_size(self, client: AsyncClient, valid_api_key: str):
        """Test invalid page size."""
        response = await client.get(
            "/api/v1/books?page_size=150",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_get_books_filter_by_category(
        self,
        client: AsyncClient,
        valid_api_key: str,
        sample_book_category: str
    ):
        """Test filtering books by category."""
        response = await client.get(
            f"/api/v1/books?category={sample_book_category}",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "filters_applied" in data
        assert data["filters_applied"].get("category") == sample_book_category
        
        # Verify all returned books have the correct category
        for book in data["data"]:
            if book.get("category"):
                assert book["category"] == sample_book_category
    
    @pytest.mark.asyncio
    async def test_get_books_filter_by_price_range(self, client: AsyncClient, valid_api_key: str):
        """Test filtering books by price range."""
        response = await client.get(
            "/api/v1/books?min_price=10&max_price=50",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "filters_applied" in data
        
        # Verify all returned books are within price range
        for book in data["data"]:
            if book.get("price_incl_tax") is not None:
                assert 10 <= book["price_incl_tax"] <= 50
    
    @pytest.mark.asyncio
    async def test_get_books_filter_by_min_rating(self, client: AsyncClient, valid_api_key: str):
        """Test filtering books by minimum rating."""
        response = await client.get(
            "/api/v1/books?min_rating=4",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned books meet minimum rating
        for book in data["data"]:
            if book.get("rating") is not None:
                assert book["rating"] >= 4
    
    @pytest.mark.asyncio
    async def test_get_books_filter_by_availability(self, client: AsyncClient, valid_api_key: str):
        """Test filtering books by availability."""
        response = await client.get(
            "/api/v1/books?availability=In%20stock",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify returned books contain availability text
        for book in data["data"]:
            if book.get("availability"):
                assert "In stock" in book["availability"]
    
    @pytest.mark.asyncio
    async def test_get_books_search(self, client: AsyncClient, valid_api_key: str):
        """Test text search in books."""
        response = await client.get(
            "/api/v1/books?search=the",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "filters_applied" in data
        # Should return some results
        assert len(data["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_books_combined_filters(
        self,
        client: AsyncClient,
        valid_api_key: str,
        sample_book_category: str
    ):
        """Test combining multiple filters."""
        response = await client.get(
            f"/api/v1/books?category={sample_book_category}&min_rating=3&max_price=100",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "filters_applied" in data
        filters = data["filters_applied"]
        assert "category" in filters or "min_rating" in filters or "max_price" in filters
    
    @pytest.mark.asyncio
    async def test_get_books_sort_by_title(self, client: AsyncClient, valid_api_key: str):
        """Test sorting books by title."""
        response = await client.get(
            "/api/v1/books?sort_by=title&page_size=5",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        titles = [book["title"] for book in data["data"]]
        assert titles == sorted(titles)
    
    @pytest.mark.asyncio
    async def test_get_books_sort_by_price_asc(self, client: AsyncClient, valid_api_key: str):
        """Test sorting books by price ascending."""
        response = await client.get(
            "/api/v1/books?sort_by=price_asc&page_size=5",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        prices = [book.get("price_incl_tax") for book in data["data"] if book.get("price_incl_tax")]
        if len(prices) > 1:
            assert prices == sorted(prices)
    
    @pytest.mark.asyncio
    async def test_get_books_sort_by_price_desc(self, client: AsyncClient, valid_api_key: str):
        """Test sorting books by price descending."""
        response = await client.get(
            "/api/v1/books?sort_by=price_desc&page_size=5",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        prices = [book.get("price_incl_tax") for book in data["data"] if book.get("price_incl_tax")]
        if len(prices) > 1:
            assert prices == sorted(prices, reverse=True)
    
    @pytest.mark.asyncio
    async def test_get_books_sort_by_rating_desc(self, client: AsyncClient, valid_api_key: str):
        """Test sorting books by rating descending."""
        response = await client.get(
            "/api/v1/books?sort_by=rating_desc&page_size=5",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        ratings = [book.get("rating") for book in data["data"] if book.get("rating")]
        if len(ratings) > 1:
            assert ratings == sorted(ratings, reverse=True)
    
    @pytest.mark.asyncio
    async def test_get_books_sort_by_recent(self, client: AsyncClient, valid_api_key: str):
        """Test sorting books by most recent."""
        response = await client.get(
            "/api/v1/books?sort_by=recent&page_size=5",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_books_invalid_sort(self, client: AsyncClient, valid_api_key: str):
        """Test invalid sort parameter."""
        response = await client.get(
            "/api/v1/books?sort_by=invalid_sort",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_books_response_structure(self, client: AsyncClient, valid_api_key: str):
        """Test the structure of the response."""
        response = await client.get(
            "/api/v1/books?page_size=1",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level structure
        assert "data" in data
        assert "pagination" in data
        
        # Check pagination structure
        pagination = data["pagination"]
        required_pagination_fields = ["total", "page", "page_size", "total_pages", "has_next", "has_prev"]
        for field in required_pagination_fields:
            assert field in pagination
        
        # Check book structure if any books returned
        if data["data"]:
            book = data["data"][0]
            required_book_fields = ["id", "title", "source_url", "crawl_timestamp"]
            for field in required_book_fields:
                assert field in book
    
    @pytest.mark.asyncio
    async def test_get_books_rate_limit_headers(self, client: AsyncClient, valid_api_key: str):
        """Test that rate limit headers are present."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
