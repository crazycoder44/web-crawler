"""Mocking utilities for MongoDB operations."""

from typing import Any, List
from unittest.mock import AsyncMock

class AsyncCursorMock:
    def __init__(self, documents: List[Any]):
        self._documents = documents

    async def to_list(self, length=None) -> List[Any]:
        return self._documents

class AsyncCollectionMock(AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._documents = []

    def configure_mock(self, documents: List[Any]):
        """Configure the mock with a list of documents."""
        self._documents = documents
        
        async def mock_aggregate(*args, **kwargs):
            return AsyncCursorMock(self._documents)
            
        self.aggregate.side_effect = mock_aggregate