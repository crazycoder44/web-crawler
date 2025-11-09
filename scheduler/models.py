# scheduler/models.py

"""
Models for tracking changes in book data.
Integrates with the crawler's existing change tracking system.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom type for handling MongoDB ObjectId in Pydantic models."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception as e:
                raise ValueError('Invalid ObjectId') from e
        if isinstance(v, dict):
            try:
                return ObjectId(v.get('$oid', v.get('_id', v)))
            except Exception as e:
                raise ValueError('Invalid ObjectId') from e
        raise TypeError('String, ObjectId or dict required')
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Treat PyObjectId as ObjectId type."""
        return handler(ObjectId)


class BookChange(BaseModel):
    """Represents a change in book data, aligned with crawler's change tracking."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    book_id: PyObjectId = Field(..., description="ID of the book that changed")
    changes: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Changes in format: {field: {'old': old_value, 'new': new_value}}"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    change_type: str = Field(
        'update',
        description="Type of change: 'update', 'new', or 'consolidated'"
    )


class ConsolidatedChanges(BaseModel):
    """Represents consolidated changes for storage optimization."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    book_id: PyObjectId
    change_count: int
    date_range: List[datetime]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DailyChangeReport(BaseModel):
    """Daily report of all changes."""
    date: datetime = Field(default_factory=datetime.utcnow)
    total_books: int = Field(0, description="Total number of books")
    new_books: int = Field(0, description="Number of new books")
    updated_books: int = Field(0, description="Number of updated books")
    changes_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of changes by field type"
    )
    error_count: int = Field(0, description="Number of errors encountered")
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metrics like response times, success rates"
    )


class ChangeRecord(BaseModel):
    """Detailed record of a single change event."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    book_id: PyObjectId = Field(..., description="ID of the book that changed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changes: Dict[str, Any] = Field(
        ...,
        description="Details of what changed: field, old_value, new_value, change_type"
    )