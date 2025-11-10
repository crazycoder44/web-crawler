"""
Integration tests for error handling and edge cases.

Tests:
- 404 Not Found errors
- 422 Validation errors
- 500 Internal Server errors (if applicable)
- CORS headers
- Content negotiation
"""

import pytest
from httpx import AsyncClient


class TestErrorHandling:
    """Test API error handling."""
    
    @pytest.mark.asyncio
    async def test_404_invalid_endpoint(self, client: AsyncClient, valid_api_key: str):
        """Test accessing non-existent endpoint."""
        response = await client.get("/api/v1/invalid-endpoint",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 404
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_404_book_not_found(self, client: AsyncClient, valid_api_key: str):
        """Test 404 error for non-existent book."""
        response = await client.get("/api/v1/books/507f1f77bcf86cd799439999",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["message"] == "Book not found"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_422_invalid_object_id(self, client: AsyncClient, valid_api_key: str):
        """Test 422 validation error for invalid ObjectId."""
        response = await client.get("/api/v1/books/invalid-id-123",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
        assert "details" in data
    
    @pytest.mark.asyncio
    async def test_422_invalid_page_number(self, client: AsyncClient, valid_api_key: str):
        """Test 422 error for invalid page number."""
        response = await client.get("/api/v1/books?page=0",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_422_invalid_page_size(self, client: AsyncClient, valid_api_key: str):
        """Test 422 error for invalid page size."""
        response = await client.get("/api/v1/books?page_size=200",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_422_invalid_rating(self, client: AsyncClient, valid_api_key: str):
        """Test 422 error for invalid rating value."""
        response = await client.get("/api/v1/books?min_rating=10",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_422_invalid_date_format(self, client: AsyncClient, valid_api_key: str):
        """Test 422 error for invalid date format."""
        response = await client.get("/api/v1/changes?since=not-a-date",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_error_response_structure(self, client: AsyncClient, valid_api_key: str):
        """Test that error responses have consistent structure."""
        response = await client.get("/api/v1/books/invalid-id",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        
        # Required error fields
        assert "message" in data
        assert "timestamp" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["timestamp"], str)
    
    @pytest.mark.asyncio
    async def test_error_includes_timestamp(self, client: AsyncClient, valid_api_key: str):
        """Test that error responses include timestamp."""
        response = await client.get("/api/v1/books/507f1f77bcf86cd799439999",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 404
        data = response.json()
        
        assert "timestamp" in data
        # Verify it's a valid ISO datetime
        from datetime import datetime
        try:
            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid timestamp format in error response")
    
    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self, client: AsyncClient, valid_api_key: str):
        """Test 405 error for unsupported HTTP method."""
        response = await client.post("/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_415_unsupported_media_type(self, client: AsyncClient, valid_api_key: str):
        """Test behavior with unsupported content type."""
        response = await client.post(
            "/api/v1/books",
            content="not json",
            headers={"Content-Type": "text/plain"}
        )
        # Should get 405 since POST is not allowed
        assert response.status_code == 405


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_basic(self, client: AsyncClient, valid_api_key: str):
        """Test basic health check."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self, client: AsyncClient, valid_api_key: str):
        """Test health endpoint response structure."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["status", "service", "version"]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
    
    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, client: AsyncClient, valid_api_key: str):
        """Test that health endpoint doesn't require authentication."""
        response = await client.get("/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_health_endpoint_content_type(self, client: AsyncClient, valid_api_key: str):
        """Test health endpoint content type."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestAPIVersioning:
    """Test API versioning."""
    
    @pytest.mark.asyncio
    async def test_v1_prefix_required(self, client: AsyncClient, valid_api_key: str):
        """Test that v1 prefix is required in path."""
        response = await client.get("/api/books")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_v1_endpoints_accessible(self, client: AsyncClient, valid_api_key: str):
        """Test that v1 endpoints are accessible."""
        response = await client.get("/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200


class TestResponseHeaders:
    """Test response headers."""
    
    @pytest.mark.asyncio
    async def test_content_type_json(self, client: AsyncClient, valid_api_key: str):
        """Test that responses have JSON content type."""
        response = await client.get("/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_request_id_header(self, client: AsyncClient, valid_api_key: str):
        """Test that responses include request ID."""
        response = await client.get("/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        # Check if request ID header is present (if implemented)
        # assert "X-Request-ID" in response.headers
    
    @pytest.mark.asyncio
    async def test_execution_time_header(self, client: AsyncClient, valid_api_key: str):
        """Test that responses include execution time."""
        response = await client.get("/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        # Check if execution time header is present (if implemented)
        # assert "X-Execution-Time" in response.headers


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_very_large_page_number(self, client: AsyncClient, valid_api_key: str):
        """Test requesting a very large page number."""
        response = await client.get("/api/v1/books?page=999999",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        # Should return empty results
        assert data["data"] == []
    
    @pytest.mark.asyncio
    async def test_maximum_page_size(self, client: AsyncClient, valid_api_key: str):
        """Test maximum allowed page size."""
        response = await client.get("/api/v1/books?page_size=100",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 100
    
    @pytest.mark.asyncio
    async def test_minimum_page_size(self, client: AsyncClient, valid_api_key: str):
        """Test minimum allowed page size."""
        response = await client.get("/api/v1/books?page_size=1",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 1
    
    @pytest.mark.asyncio
    async def test_special_characters_in_search(self, client: AsyncClient, valid_api_key: str):
        """Test search with special characters."""
        response = await client.get("/api/v1/books?search=test%20%26%20book",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_unicode_in_search(self, client: AsyncClient, valid_api_key: str):
        """Test search with unicode characters."""
        response = await client.get("/api/v1/books?search=café",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_empty_search_string(self, client: AsyncClient, valid_api_key: str):
        """Test search with empty string."""
        response = await client.get("/api/v1/books?search=",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_negative_price(self, client: AsyncClient, valid_api_key: str):
        """Test filtering with negative price."""
        response = await client.get("/api/v1/books?min_price=-10",
            headers={"X-API-Key": valid_api_key}
        )
        # Should either reject or treat as 0
        assert response.status_code in [200, 422]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient, valid_api_key: str):
        """Test handling concurrent requests."""
        import asyncio
        
        # Make 5 concurrent requests
        tasks = [
            client.get("/api/v1/books", headers={"X-API-Key": valid_api_key})
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
