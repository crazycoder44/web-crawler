"""
Unit Tests for Rate Limiting

Tests rate limit store, sliding window algorithm, and middleware.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from src.api.middleware.rate_limiter import RateLimitStore, RateLimitMiddleware


class TestRateLimitStore:
    """Test RateLimitStore class."""
    
    @pytest.mark.asyncio
    async def test_initial_request_count(self):
        """Test initial request count is zero."""
        store = RateLimitStore()
        count = await store.get_request_count("test_key", 3600)
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_record_single_request(self):
        """Test recording a single request."""
        store = RateLimitStore()
        await store.record_request("test_key")
        
        count = await store.get_request_count("test_key", 3600)
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_record_multiple_requests(self):
        """Test recording multiple requests."""
        store = RateLimitStore()
        
        for _ in range(5):
            await store.record_request("test_key")
        
        count = await store.get_request_count("test_key", 3600)
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_separate_keys(self):
        """Test that different keys have separate counts."""
        store = RateLimitStore()
        
        await store.record_request("key1")
        await store.record_request("key1")
        await store.record_request("key2")
        
        count1 = await store.get_request_count("key1", 3600)
        count2 = await store.get_request_count("key2", 3600)
        
        assert count1 == 2
        assert count2 == 1
    
    @pytest.mark.asyncio
    async def test_sliding_window(self):
        """Test sliding window removes old requests."""
        store = RateLimitStore()
        
        # Record request and manually set old timestamp
        await store.record_request("test_key")
        
        # Manually add an old timestamp (outside window)
        old_time = datetime.utcnow() - timedelta(hours=2)
        store._requests["test_key"].appendleft(old_time)
        
        # Count with 1 hour window should only include recent request
        count = await store.get_request_count("test_key", 3600)
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup of expired requests."""
        store = RateLimitStore()
        
        # Add requests with old timestamps
        old_time = datetime.utcnow() - timedelta(hours=2)
        store._requests["test_key"] = asyncio.Queue()
        
        # Manually add old requests
        from collections import deque
        store._requests["test_key"] = deque([old_time, old_time])
        
        # Add recent request
        await store.record_request("test_key")
        
        # Cleanup with 1 hour window
        await store.cleanup_expired(3600)
        
        # Should only have recent request
        count = await store.get_request_count("test_key", 3600)
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_removes_empty_keys(self):
        """Test cleanup removes keys with no requests."""
        store = RateLimitStore()
        
        # Add old request
        old_time = datetime.utcnow() - timedelta(hours=2)
        from collections import deque
        store._requests["test_key"] = deque([old_time])
        
        # Cleanup should remove the key
        await store.cleanup_expired(3600)
        
        assert "test_key" not in store._requests


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class."""
    
    def test_middleware_initialization(self):
        """Test middleware initializes with correct settings."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            assert middleware.rate_limit == 100
            assert middleware.window_seconds == 3600
    
    def test_is_exempt_health_endpoint(self):
        """Test health endpoint is exempt from rate limiting."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            assert middleware.is_exempt("/health") is True
            assert middleware.is_exempt("/docs") is True
            assert middleware.is_exempt("/redoc") is True
            assert middleware.is_exempt("/openapi.json") is True
    
    def test_is_not_exempt_regular_endpoint(self):
        """Test regular endpoints are not exempt."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            assert middleware.is_exempt("/books") is False
            assert middleware.is_exempt("/changes") is False
            assert middleware.is_exempt("/api/v1/data") is False
    
    @pytest.mark.asyncio
    async def test_dispatch_exempt_path(self):
        """Test dispatch allows exempt paths without checking rate limit."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            # Mock request and response
            request = Mock()
            request.url.path = "/health"
            
            response = Mock()
            call_next = AsyncMock(return_value=response)
            
            result = await middleware.dispatch(request, call_next)
            
            assert result == response
            call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dispatch_no_api_key(self):
        """Test dispatch without API key."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            # Mock request without API key
            request = Mock()
            request.url.path = "/books"
            request.headers.get = Mock(return_value=None)
            
            response = Mock()
            response.headers = {}
            call_next = AsyncMock(return_value=response)
            
            result = await middleware.dispatch(request, call_next)
            
            assert "X-RateLimit-Limit" in result.headers
            assert result.headers["X-RateLimit-Remaining"] == "N/A"
    
    @pytest.mark.asyncio
    async def test_dispatch_with_valid_key_under_limit(self):
        """Test dispatch with valid key under rate limit."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            # Mock request with API key
            request = Mock()
            request.url.path = "/books"
            request.headers.get = Mock(return_value="test_key")
            
            response = Mock()
            response.headers = {}
            call_next = AsyncMock(return_value=response)
            
            # Mock rate limit store
            with patch('src.api.middleware.rate_limiter.rate_limit_store') as mock_store:
                mock_store.get_request_count = AsyncMock(return_value=50)
                mock_store.record_request = AsyncMock()
                
                result = await middleware.dispatch(request, call_next)
                
                assert "X-RateLimit-Limit" in result.headers
                assert "X-RateLimit-Remaining" in result.headers
                mock_store.record_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_exceeded(self):
        """Test dispatch when rate limit is exceeded."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            # Mock request
            request = Mock()
            request.url.path = "/books"
            request.headers.get = Mock(return_value="test_key")
            
            # Mock rate limit store showing limit exceeded
            with patch('src.api.middleware.rate_limiter.rate_limit_store') as mock_store:
                with patch('src.api.middleware.rate_limiter.log_rate_limit'):
                    mock_store.get_request_count = AsyncMock(return_value=100)
                    
                    call_next = AsyncMock()
                    result = await middleware.dispatch(request, call_next)
                    
                    # Should return 429 response
                    assert result.status_code == 429
                    assert "Retry-After" in result.headers
                    assert result.headers["X-RateLimit-Remaining"] == "0"
                    
                    # Should not call next handler
                    call_next.assert_not_called()


class TestRateLimitIntegration:
    """Test rate limiting with realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_sequential_requests_within_limit(self):
        """Test sequential requests stay within limit."""
        store = RateLimitStore()
        
        # Make 10 requests
        for _ in range(10):
            await store.record_request("test_key")
        
        count = await store.get_request_count("test_key", 3600)
        assert count == 10
    
    @pytest.mark.asyncio
    async def test_requests_across_time_window(self):
        """Test requests are counted within sliding window."""
        store = RateLimitStore()
        
        # Add old request (outside 1 hour window)
        from collections import deque
        old_time = datetime.utcnow() - timedelta(hours=1, minutes=5)
        store._requests["test_key"] = deque([old_time])
        
        # Add new request
        await store.record_request("test_key")
        
        # Only new request should count
        count = await store.get_request_count("test_key", 3600)
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_different_keys(self):
        """Test concurrent requests for different keys."""
        store = RateLimitStore()
        
        # Simulate concurrent requests
        tasks = [
            store.record_request("key1"),
            store.record_request("key2"),
            store.record_request("key1"),
            store.record_request("key3"),
            store.record_request("key2"),
        ]
        
        await asyncio.gather(*tasks)
        
        count1 = await store.get_request_count("key1", 3600)
        count2 = await store.get_request_count("key2", 3600)
        count3 = await store.get_request_count("key3", 3600)
        
        assert count1 == 2
        assert count2 == 2
        assert count3 == 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_reset(self):
        """Test rate limit resets after time window."""
        store = RateLimitStore()
        
        # Fill up rate limit
        for _ in range(100):
            await store.record_request("test_key")
        
        count_before = await store.get_request_count("test_key", 3600)
        assert count_before == 100
        
        # Cleanup old requests (simulate time passing)
        old_time = datetime.utcnow() - timedelta(hours=2)
        from collections import deque
        store._requests["test_key"] = deque([old_time] * 100)
        
        count_after = await store.get_request_count("test_key", 3600)
        assert count_after == 0


class TestRateLimitHeaders:
    """Test rate limit response headers."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self):
        """Test that rate limit headers are added to response."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            request = Mock()
            request.url.path = "/books"
            request.headers.get = Mock(return_value="test_key")
            
            response = Mock()
            response.headers = {}
            call_next = AsyncMock(return_value=response)
            
            with patch('src.api.middleware.rate_limiter.rate_limit_store') as mock_store:
                mock_store.get_request_count = AsyncMock(return_value=50)
                mock_store.record_request = AsyncMock()
                
                result = await middleware.dispatch(request, call_next)
                
                assert "X-RateLimit-Limit" in result.headers
                assert "X-RateLimit-Remaining" in result.headers
                assert "X-RateLimit-Reset" in result.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_headers(self):
        """Test headers when rate limit is exceeded."""
        app = Mock()
        
        with patch('src.api.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_per_hour = 100
            middleware = RateLimitMiddleware(app)
            
            request = Mock()
            request.url.path = "/books"
            request.headers.get = Mock(return_value="test_key")
            
            with patch('src.api.middleware.rate_limiter.rate_limit_store') as mock_store:
                with patch('src.api.middleware.rate_limiter.log_rate_limit'):
                    mock_store.get_request_count = AsyncMock(return_value=100)
                    
                    call_next = AsyncMock()
                    result = await middleware.dispatch(request, call_next)
                    
                    assert result.headers["X-RateLimit-Remaining"] == "0"
                    assert "Retry-After" in result.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


