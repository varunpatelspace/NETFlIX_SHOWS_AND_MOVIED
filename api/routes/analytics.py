"""
Analytics and dashboard summary endpoints for Netflix Live Content Analytics API.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends

from analytics.analytics_service import AnalyticsService
from api.dependencies import get_analytics_service, get_analytics_filters
from api.schemas.analytics import DashboardSummaryResponse, OverviewMetrics, InsightItem

router = APIRouter(prefix="/api/v1", tags=["Analytics"])


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="Composite Dashboard Summary",
    description="Fetch consolidated analytics (overview, content, temporal, geographic, ratings, duration, and insights) in a single request."
)
def get_dashboard_summary(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve complete dashboard metrics suite."""
    return service.get_dashboard_summary(filters=filters)


@router.get(
    "/analytics/overview",
    response_model=OverviewMetrics,
    summary="Catalog Overview KPIs",
    description="Fetch high-level catalog KPIs: totals, format ratios, release spans, and freshness."
)
def get_overview(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve catalog overview metrics."""
    return service.get_overview(filters=filters)


@router.get(
    "/analytics/content",
    summary="Content Types & Genre Analysis",
    description="Fetch content format split, top genres overall, movie genres, and TV genres."
)
def get_content(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve content type and genre distributions."""
    return service.get_content_analysis(filters=filters)


@router.get(
    "/analytics/temporal",
    summary="Temporal Trends & Ingestion Seasonality",
    description="Fetch historical release trends, addition growth trajectories, monthly seasonality, and licensing lag."
)
def get_temporal(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve temporal and growth analytics."""
    return service.get_temporal_analysis(filters=filters)


@router.get(
    "/analytics/geographic",
    summary="Geographic Production Footprint",
    description="Fetch top content producing countries, primary territory hubs, and international co-production rates."
)
def get_geographic(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve geographic and international co-production analytics."""
    return service.get_geographic_analysis(filters=filters)


@router.get(
    "/analytics/ratings",
    summary="Ratings & Demographics Distribution",
    description="Fetch certification ratings breakdown and 5-tier audience demographic classifications."
)
def get_ratings(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve certification ratings and demographic analytics."""
    return service.get_rating_analysis(filters=filters)


@router.get(
    "/analytics/duration",
    summary="Duration & Longevity Analysis",
    description="Fetch movie runtime statistics/tiers and TV show season distribution/longevity."
)
def get_duration(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve duration and longevity metrics."""
    return service.get_duration_analysis(filters=filters)


@router.get(
    "/analytics/insights",
    response_model=List[InsightItem],
    summary="Rule-Based Business Insights",
    description="Fetch deterministic, evidence-based business observations synthesized from catalog data."
)
def get_insights(
    service: AnalyticsService = Depends(get_analytics_service),
    filters: Dict[str, Any] = Depends(get_analytics_filters)
):
    """Retrieve automatically generated catalog insights."""
    return service.get_all_insights(filters=filters)
