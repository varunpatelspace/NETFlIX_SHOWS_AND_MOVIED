"""
Content browsing and detail endpoints for Netflix catalog titles.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from database.repository import NetflixRepository
from api.dependencies import get_repository, get_analytics_filters
from api.schemas.content import ContentItem, PaginatedContent

router = APIRouter(prefix="/api/v1", tags=["Content"])


@router.get(
    "/content",
    response_model=PaginatedContent,
    summary="Browse & Filter Catalog Titles",
    description="Retrieve paginated list of catalog titles with comprehensive multi-criteria filtering."
)
def list_content(
    limit: int = Query(50, ge=1, le=500, description="Max titles to return per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: Optional[str] = Query(None, description="Search keyword in title, director, or cast"),
    filters: Dict[str, Any] = Depends(get_analytics_filters),
    repo: NetflixRepository = Depends(get_repository)
):
    """Retrieve paginated content titles with optional filters and keyword search."""
    # Fetch paginated records via repository
    records = repo.get_all(
        limit=limit,
        offset=offset,
        content_type=filters.get("content_type"),
        min_year=filters.get("release_year_min"),
        max_year=filters.get("release_year_max"),
        country=filters.get("country"),
        genre=filters.get("genre"),
        rating=filters.get("rating"),
        age_group=filters.get("age_group"),
        search=search
    )

    # Compute total matching records using lightweight count
    total_matching = len(repo.get_all(
        content_type=filters.get("content_type"),
        min_year=filters.get("release_year_min"),
        max_year=filters.get("release_year_max"),
        country=filters.get("country"),
        genre=filters.get("genre"),
        rating=filters.get("rating"),
        age_group=filters.get("age_group"),
        search=search
    ))

    items = [ContentItem.model_validate(r) for r in records]

    return PaginatedContent(
        total=total_matching,
        limit=limit,
        offset=offset,
        data=items
    )


@router.get(
    "/content/{show_id}",
    response_model=ContentItem,
    summary="Get Title Details by show_id",
    description="Retrieve full details and engineered attributes for a single catalog title by its unique show_id."
)
def get_content_by_id(
    show_id: str,
    repo: NetflixRepository = Depends(get_repository)
):
    """Retrieve detailed title information by show_id."""
    record = repo.get_by_show_id(show_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with show_id '{show_id}' was not found"
        )
    return ContentItem.model_validate(record)
