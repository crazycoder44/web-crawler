from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

class Book(BaseModel):
    source_url: HttpUrl
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price_incl_tax: Optional[float] = Field(None, gt=0)
    price_excl_tax: Optional[float] = Field(None, gt=0)
    availability: Optional[str] = None
    num_reviews: Optional[int] = Field(None, ge=0)
    image_url: Optional[HttpUrl] = None
    rating: Optional[int] = Field(None, ge=0, le=5)
    raw_html_hash: str = Field(alias='fingerprint')  # For compatibility with existing code
    raw_html_snapshot_path: Optional[str] = None
    crawl_timestamp: datetime
    status: str = Field("ok", description="ok, error, or retry")
    response_time: Optional[float] = None  # Request-response time in seconds
    http_status: Optional[int] = Field(None, ge=100, le=599)
    id: Optional[str] = None  # Add ID field that will be set by store
