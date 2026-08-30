"""
Route modules for Netflix Live Content Analytics API.
"""

from api.routes.health import router as health_router
from api.routes.analytics import router as analytics_router
from api.routes.content import router as content_router
from api.routes.pipeline import router as pipeline_router

__all__ = [
    "health_router",
    "analytics_router",
    "content_router",
    "pipeline_router",
]
