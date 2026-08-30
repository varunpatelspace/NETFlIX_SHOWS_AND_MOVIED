"""
Analytics package for Netflix Live Content Analytics Platform.
"""

from analytics.analytics_service import AnalyticsService
from analytics.overview import get_catalog_overview
from analytics.content_analysis import get_content_analysis
from analytics.temporal_analysis import get_temporal_analysis
from analytics.geographic_analysis import get_geographic_analysis
from analytics.rating_analysis import get_rating_analysis
from analytics.duration_analysis import get_duration_analysis
from analytics.insights import generate_catalog_insights

__all__ = [
    "AnalyticsService",
    "get_catalog_overview",
    "get_content_analysis",
    "get_temporal_analysis",
    "get_geographic_analysis",
    "get_rating_analysis",
    "get_duration_analysis",
    "generate_catalog_insights",
]
