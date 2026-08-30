"""
Health check and system status endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from database.repository import NetflixRepository
from api.dependencies import get_repository
from api.schemas.pipeline import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Database Connectivity",
    description="Check API availability, database connection health, and current record count."
)
def get_health(repo: NetflixRepository = Depends(get_repository)):
    """Check health and database connectivity."""
    try:
        record_count = repo.get_total_count()
        return HealthResponse(
            status="healthy",
            database="connected",
            database_record_count=record_count,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0"
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "database_record_count": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0",
                "detail": str(e)
            }
        )
