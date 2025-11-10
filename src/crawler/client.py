"""Async HTTP client with retry logic and rate limiting."""
import asyncio
import httpx
from typing import Tuple, Optional
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception_type
)
from .settings import Settings
import logging

logger = logging.getLogger("books_crawler")
settings = Settings()

class CrawlerClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            headers={'User-Agent': settings.user_agent},
            follow_redirects=True
        )
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()  # For rate limiting

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch(self, url: str) -> Tuple[int, str, str]:
        """Fetch a URL with retry logic and rate limiting.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Tuple of (status_code, html_content, final_url)
            
        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        # Rate limiting
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_request_time
            if time_since_last < settings.request_interval:
                delay = settings.request_interval - time_since_last
                await asyncio.sleep(delay)
            
            try:
                response = await self.client.get(url)
                self.last_request_time = asyncio.get_event_loop().time()
                
                # Raise for 5xx errors but not 4xx
                if response.status_code >= 500:
                    response.raise_for_status()
                elif response.status_code >= 400:
                    logger.error(f"Client error {response.status_code} for {url}")
                    return response.status_code, "", str(response.url)
                
                return response.status_code, response.text, str(response.url)
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"Server error {e.response.status_code} for {url}")
                raise  # Will be retried
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                logger.warning(f"Network/timeout error for {url}: {str(e)}")
                raise  # Will be retried
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {str(e)}")
                raise