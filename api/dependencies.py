"""
FastAPI dependency injection providers for Netflix Live Content Analytics Platform.
"""

from typing import Dict, Any, Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from database.database import get_db
from database.repository import NetflixRepository
from analytics.analytics_service import AnalyticsService


def get_repository(db: Session = Depends(get_db)) -> NetflixRepository:
    """Dependency provider for database repository."""
    return NetflixRepository(db)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency provider for the unified analytics service."""
    return AnalyticsService(db)


def get_analytics_filters(
    content_type: Optional[str] = Query(None, description="Filter by 'Movie', 'TV Show', or 'All'"),
    release_year_min: Optional[int] = Query(None, description="Minimum release year"),
    release_year_max: Optional[int] = Query(None, description="Maximum release year"),
    country: Optional[str] = Query(None, description="Country name substring"),
    genre: Optional[str] = Query(None, description="Genre substring"),
    rating: Optional[str] = Query(None, description="Certification rating (e.g., 'TV-MA', 'PG-13')"),
    age_group: Optional[str] = Query(None, description="Target demographic tier (e.g., 'Adults (18+)')")
) -> Dict[str, Any]:
    """
    Centralized query parameter extractor that builds standard filter criteria.
    """
    filters: Dict[str, Any] = {}
    if content_type:
        filters["content_type"] = content_type
    if release_year_min is not None:
        filters["release_year_min"] = release_year_min
    if release_year_max is not None:
        filters["release_year_max"] = release_year_max
    if country:
        filters["country"] = country
    if genre:
        filters["genre"] = genre
    if rating:
        filters["rating"] = rating
    if age_group:
        filters["age_group"] = age_group

    return filters
