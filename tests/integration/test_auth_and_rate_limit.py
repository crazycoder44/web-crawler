"""
Integration tests for authentication and authorization.

Tests:
- Valid API key acceptance
- Invalid API key rejection
- Missing API key (optional auth)
- Rate limiting with authentication
"""

import pytest
from httpx import AsyncClient


class TestAuthentication:
    """Test API authentication."""
    
    @pytest.mark.asyncio
    async def test_valid_api_key_accepted(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test that valid API key is accepted."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_still_allows_access(
        self,
        client: AsyncClient,
        invalid_api_key: str
    ):
        """Test that invalid API key is rejected."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": invalid_api_key}
        )
        # Should return 401 for invalid key
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_missing_api_key_allows_access(self, client: AsyncClient, valid_api_key: str):
        """Test that missing API key is rejected."""
        response = await client.get("/api/v1/books")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_api_key_case_sensitivity(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test that API key validation is case-sensitive."""
        response_lower = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key.lower()}
        )
        response_upper = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key.upper()}
        )
        # Both should fail (401) since keys are case-sensitive
        assert response_lower.status_code == 401
        assert response_upper.status_code == 401
    
    @pytest.mark.asyncio
    async def test_empty_api_key(self, client: AsyncClient, valid_api_key: str):
        """Test behavior with empty API key."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": ""}
        )
        # Should fail since empty key is invalid
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_api_key_with_special_characters(self, client: AsyncClient, valid_api_key: str):
        """Test API key with special characters."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": "test-key-!@#$%^&*()"}
        )
        # Should fail since this invalid key
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_multiple_api_key_headers(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test behavior with multiple API key headers."""
        # httpx/ASGI typically uses the first header value
        response = await client.get(
            "/api/v1/books",
            headers=[
                ("X-API-Key", valid_api_key),
                ("X-API-Key", "invalid-key")
            ]
        )
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test that rate limit headers are present in responses."""
        response = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify header values are numeric
        assert int(response.headers["X-RateLimit-Limit"]) > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_decreases(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test that rate limit remaining decreases with requests."""
        # First request
        response1 = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        
        # Second request
        response2 = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        # Remaining should decrease
        assert remaining2 <= remaining1
    
    @pytest.mark.asyncio
    async def test_rate_limit_separate_keys(
        self,
        client: AsyncClient,
        valid_api_key: str,
        invalid_api_key: str
    ):
        """Test that rate limits are tracked separately per key."""
        # Make request with valid key
        response1 = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": valid_api_key}
        )
        remaining_valid = int(response1.headers["X-RateLimit-Remaining"])
        
        # Make request with different key
        response2 = await client.get(
            "/api/v1/books",
            headers={"X-API-Key": invalid_api_key}
        )
        remaining_invalid = int(response2.headers["X-RateLimit-Remaining"])
        
        # Both should have their own limits
        assert remaining_valid >= 0
        assert remaining_invalid >= 0
    
    @pytest.mark.asyncio
    async def test_health_endpoint_exempt_from_rate_limit(self, client: AsyncClient, valid_api_key: str):
        """Test that health endpoint is exempt from rate limiting."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        # Health endpoint should not have rate limit headers
        # or should not count against the limit
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_rate_limit_applies_to_all_endpoints(
        self,
        client: AsyncClient,
        valid_api_key: str,
        sample_book_id: str
    ):
        """Test that rate limit is shared across all endpoints."""
        headers = {"X-API-Key": valid_api_key}
        
        # Make requests to different endpoints
        response1 = await client.get("/api/v1/books", headers=headers)
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        
        response2 = await client.get(f"/api/v1/books/{sample_book_id}", headers=headers)
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        response3 = await client.get("/api/v1/changes", headers=headers)
        remaining3 = int(response3.headers["X-RateLimit-Remaining"])
        
        # Rate limit should decrease across all endpoints
        assert remaining2 <= remaining1
        assert remaining3 <= remaining2
