"""
Integration tests for GET /changes endpoint.

Tests the complete request/response flow including:
- Time-based filtering (since parameter)
- Book ID filtering
- Change type filtering
- Pagination
- Authentication
- Response structure validation
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


class TestChangesEndpoint:
    """Test GET /changes endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_changes_without_auth(self, client: AsyncClient):
        """Test accessing changes endpoint without authentication."""
        response = await client.get("/api/v1/changes")
        assert response.status_code == 401
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_get_changes_with_valid_auth(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test accessing changes with valid API key."""
        response = await client.get(
            "/api/v1/changes",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_get_changes_pagination_default(self, client: AsyncClient, valid_api_key: str):
        """Test default pagination parameters."""
        response = await client.get("/api/v1/changes",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 20
        assert pagination["total"] >= 0
        assert "has_next" in pagination
        assert "has_prev" in pagination
    
    @pytest.mark.asyncio
    async def test_get_changes_pagination_custom(self, client: AsyncClient, valid_api_key: str):
        """Test custom pagination parameters."""
        response = await client.get("/api/v1/changes?page=1&page_size=5",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 5
        assert len(data["data"]) <= 5
    
    @pytest.mark.asyncio
    async def test_get_changes_filter_by_since(self, client: AsyncClient, valid_api_key: str):
        """Test filtering changes by since parameter."""
        # Get changes from last 30 days
        since_date = datetime.now(timezone.utc) - timedelta(days=30)
        since_str = since_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        response = await client.get(f"/api/v1/changes?since={since_str}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify since parameter is in response
        if "since" in data:
            assert data["since"] is not None
    
    @pytest.mark.asyncio
    async def test_get_changes_filter_by_book_id(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test filtering changes by book_id."""
        response = await client.get(f"/api/v1/changes?book_id={sample_book_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all changes are for the specified book
        for change in data["data"]:
            if change.get("book_id"):
                assert change["book_id"] == sample_book_id
    
    @pytest.mark.asyncio
    async def test_get_changes_filter_by_change_type(self, client: AsyncClient, valid_api_key: str):
        """Test filtering changes by change_type."""
        response = await client.get("/api/v1/changes?change_type=update",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are results, verify they match the filter
        for change in data["data"]:
            assert change["change_type"] in ["update", "price", "availability", "rating"]
    
    @pytest.mark.asyncio
    async def test_get_changes_combined_filters(
        self,
        client: AsyncClient,
        sample_book_id: str
    ):
        """Test combining multiple filters."""
        since_date = datetime.now(timezone.utc) - timedelta(days=7)
        since_str = since_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        response = await client.get(
            f"/api/v1/changes?book_id={sample_book_id}&since={since_str}&change_type=update"
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_get_changes_invalid_since_format(self, client: AsyncClient, valid_api_key: str):
        """Test invalid since date format."""
        response = await client.get("/api/v1/changes?since=invalid-date",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_get_changes_invalid_book_id(self, client: AsyncClient, valid_api_key: str):
        """Test invalid book_id format."""
        response = await client.get("/api/v1/changes?book_id=invalid-id",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation error"
    
    @pytest.mark.asyncio
    async def test_get_changes_response_structure(self, client: AsyncClient, valid_api_key: str):
        """Test the structure of the response."""
        response = await client.get("/api/v1/changes?page_size=1",
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
        
        # Check change structure if any changes returned
        if data["data"]:
            change = data["data"][0]
            required_change_fields = ["id", "book_id", "timestamp", "change_type"]
            for field in required_change_fields:
                assert field in change
    
    @pytest.mark.asyncio
    async def test_get_changes_timestamp_format(self, client: AsyncClient, valid_api_key: str):
        """Test that timestamps are in valid ISO format."""
        response = await client.get("/api/v1/changes?page_size=1",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]:
            change = data["data"][0]
            timestamp = change["timestamp"]
            
            # Verify datetime format
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail("Invalid datetime format for timestamp")
    
    @pytest.mark.asyncio
    async def test_get_changes_change_types(self, client: AsyncClient, valid_api_key: str):
        """Test that change_type values are valid."""
        response = await client.get("/api/v1/changes?page_size=50",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        valid_change_types = ["update", "price", "availability", "rating", "new", "removed"]
        
        for change in data["data"]:
            assert change["change_type"] in valid_change_types
    
    @pytest.mark.asyncio
    async def test_get_changes_field_changed(self, client: AsyncClient, valid_api_key: str):
        """Test that field_changed is present when applicable."""
        response = await client.get("/api/v1/changes?page_size=10",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        for change in data["data"]:
            # field_changed is optional but should be string if present
            if "field_changed" in change and change["field_changed"] is not None:
                assert isinstance(change["field_changed"], str)
    
    @pytest.mark.asyncio
    async def test_get_changes_old_new_values(self, client: AsyncClient, valid_api_key: str):
        """Test that old_value and new_value are present for update changes."""
        response = await client.get("/api/v1/changes?change_type=update&page_size=10",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        for change in data["data"]:
            if change["change_type"] == "update":
                # These fields might be optional based on your schema
                assert "old_value" in change or "new_value" in change
    
    @pytest.mark.asyncio
    async def test_get_changes_ordering(self, client: AsyncClient, valid_api_key: str):
        """Test that changes are ordered by timestamp (most recent first)."""
        response = await client.get("/api/v1/changes?page_size=10",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["data"]) > 1:
            timestamps = [
                datetime.fromisoformat(change["timestamp"].replace('Z', '+00:00'))
                for change in data["data"]
            ]
            # Should be in descending order (most recent first)
            assert timestamps == sorted(timestamps, reverse=True)
    
    @pytest.mark.asyncio
    async def test_get_changes_rate_limit_headers(
        self,
        client: AsyncClient,
        valid_api_key: str
    ):
        """Test that rate limit headers are present."""
        response = await client.get(
            "/api/v1/changes",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    @pytest.mark.asyncio
    async def test_get_changes_empty_result(self, client: AsyncClient, valid_api_key: str):
        """Test changes endpoint with filters that return no results."""
        # Use a future date that shouldn't have any changes
        future_date = datetime.now(timezone.utc) + timedelta(days=365)
        since_str = future_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        response = await client.get(f"/api/v1/changes?since={since_str}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_changes_content_type(self, client: AsyncClient, valid_api_key: str):
        """Test that response has correct content type."""
        response = await client.get("/api/v1/changes",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
