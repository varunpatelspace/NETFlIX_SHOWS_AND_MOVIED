"""
Analytics response schemas for Netflix Live Content Analytics Platform.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ChartData(BaseModel):
    """Standardized chart-ready payload."""
    labels: List[Any]
    values: List[Any]
    percentages: Optional[List[float]] = None


class OverviewMetrics(BaseModel):
    """Platform overview KPIs."""
    total_titles: int
    movies: int
    tv_shows: int
    movie_percentage: float
    tv_show_percentage: float
    earliest_release_year: Optional[int] = None
    latest_release_year: Optional[int] = None
    average_release_year: Optional[float] = None
    total_countries: int
    total_genres: int
    database_freshness: Optional[str] = None


class InsightItem(BaseModel):
    """Structured rule-based observation."""
    category: str
    title: str
    description: str
    stat: str


class DashboardSummaryResponse(BaseModel):
    """Consolidated master dashboard payload."""
    filters_applied: Dict[str, Any]
    overview: Dict[str, Any]
    content: Dict[str, Any]
    temporal: Dict[str, Any]
    geographic: Dict[str, Any]
    ratings: Dict[str, Any]
    duration: Dict[str, Any]
    insights: List[InsightItem]
