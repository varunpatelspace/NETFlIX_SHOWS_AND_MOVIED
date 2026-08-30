"""
Central Analytics Service for Netflix Live Content Analytics Platform.

Coordinates all analytical modules, executes database repository queries,
applies centralized filters, and provides structured results for the
FastAPI backend and Streamlit dashboard.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from database.repository import NetflixRepository
from analytics.overview import get_catalog_overview
from analytics.content_analysis import get_content_analysis
from analytics.temporal_analysis import get_temporal_analysis
from analytics.geographic_analysis import get_geographic_analysis
from analytics.rating_analysis import get_rating_analysis
from analytics.duration_analysis import get_duration_analysis
from analytics.insights import generate_catalog_insights


class AnalyticsService:
    """
    Unified analytical service interface querying the database repository.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = NetflixRepository(db)

    def _get_filtered_df(self, filters: Optional[Dict[str, Any]] = None):
        """Helper to fetch filtered DataFrame using repository."""
        f = filters or {}
        return self.repo.get_dataframe(
            content_type=f.get("content_type"),
            min_year=f.get("release_year_min") or f.get("min_year"),
            max_year=f.get("release_year_max") or f.get("max_year"),
            country=f.get("country"),
            genre=f.get("genre"),
            rating=f.get("rating"),
            age_group=f.get("age_group")
        )

    def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get catalog overview KPIs."""
        return get_catalog_overview(self.repo, filters=filters)

    def get_content_analysis(self, filters: Optional[Dict[str, Any]] = None, top_n: int = 15) -> Dict[str, Any]:
        """Get Movies vs TV Shows and genre distribution."""
        df = self._get_filtered_df(filters)
        return get_content_analysis(df, top_n=top_n)

    def get_temporal_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get addition trends, release trajectory, and monthly seasonality."""
        df = self._get_filtered_df(filters)
        return get_temporal_analysis(df)

    def get_geographic_analysis(self, filters: Optional[Dict[str, Any]] = None, top_n: int = 15) -> Dict[str, Any]:
        """Get top producing countries and international co-production rates."""
        df = self._get_filtered_df(filters)
        return get_geographic_analysis(df, top_n=top_n)

    def get_rating_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get maturity ratings and audience demographic tiers."""
        df = self._get_filtered_df(filters)
        return get_rating_analysis(df)

    def get_duration_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get movie runtime statistics/tiers and TV show seasons distributions."""
        df = self._get_filtered_df(filters)
        return get_duration_analysis(df)

    def get_all_insights(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Synthesize all analytical modules and return human-readable insights."""
        df = self._get_filtered_df(filters)
        overview = get_catalog_overview(self.repo, filters=filters)
        content = get_content_analysis(df)
        geographic = get_geographic_analysis(df)
        temporal = get_temporal_analysis(df)
        ratings = get_rating_analysis(df)
        duration = get_duration_analysis(df)

        return generate_catalog_insights(
            overview=overview,
            content=content,
            geographic=geographic,
            temporal=temporal,
            ratings=ratings,
            duration=duration
        )

    def get_dashboard_summary(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Consolidated master endpoint returning complete metrics suite in a single call,
        optimizing backend API responses and dashboard rendering.
        """
        df = self._get_filtered_df(filters)
        overview = get_catalog_overview(self.repo, filters=filters)
        content = get_content_analysis(df)
        temporal = get_temporal_analysis(df)
        geographic = get_geographic_analysis(df)
        ratings = get_rating_analysis(df)
        duration = get_duration_analysis(df)
        insights = generate_catalog_insights(
            overview=overview,
            content=content,
            geographic=geographic,
            temporal=temporal,
            ratings=ratings,
            duration=duration
        )

        return {
            "filters_applied": filters or {},
            "overview": overview,
            "content": content,
            "temporal": temporal,
            "geographic": geographic,
            "ratings": ratings,
            "duration": duration,
            "insights": insights
        }
