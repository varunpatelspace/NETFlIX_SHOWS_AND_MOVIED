"""
Content schemas for Netflix catalog browsing and detail views.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ContentItem(BaseModel):
    """Structured representation of a Netflix catalog title."""
    model_config = ConfigDict(from_attributes=True)

    show_id: str
    type: str
    title: str
    director: Optional[str] = None
    cast: Optional[str] = None
    country: Optional[str] = None
    date_added: Optional[date] = None
    release_year: Optional[int] = None
    rating: Optional[str] = None
    duration: Optional[str] = None
    listed_in: Optional[str] = None
    description: Optional[str] = None

    # Engineered Features
    year_added: Optional[int] = None
    month_added: Optional[int] = None
    month_name_added: Optional[str] = None
    primary_country: Optional[str] = None
    is_multi_country: Optional[bool] = None
    country_count: Optional[int] = None
    duration_min: Optional[float] = None
    movie_duration_tier: Optional[str] = None
    seasons: Optional[int] = None
    age_group: Optional[str] = None
    primary_genre: Optional[str] = None
    genre_count: Optional[int] = None
    release_to_add_lag: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedContent(BaseModel):
    """Paginated catalog titles response."""
    total: int
    limit: int
    offset: int
    data: List[ContentItem]
