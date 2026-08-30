"""
Integration and Unit Tests for Netflix Live Content Analytics FastAPI Backend.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import Base, get_db
from database.repository import NetflixRepository
from api.main import app


@pytest.fixture
def client_with_isolated_db():
    """
    Creates an isolated in-memory SQLite database populated with controlled records,
    overriding the get_db dependency for deterministic testing.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Populate with sample test records
    repo = NetflixRepository(session)
    sample_records = [
        {
            "show_id": "api_1", "type": "Movie", "title": "API Film One", "release_year": 2019,
            "year_added": 2020, "month_added": 1, "month_name_added": "January",
            "country": "United States", "primary_country": "United States",
            "rating": "TV-MA", "age_group": "Adults (18+)",
            "duration": "100 min", "duration_min": 100.0, "movie_duration_tier": "90-120 min (Feature)",
            "listed_in": "Dramas, International Movies", "primary_genre": "Dramas", "genre_count": 2,
            "release_to_add_lag": 1.0, "is_multi_country": False, "country_count": 1
        },
        {
            "show_id": "api_2", "type": "TV Show", "title": "API Show Two", "release_year": 2021,
            "year_added": 2021, "month_added": 5, "month_name_added": "May",
            "country": "India", "primary_country": "India",
            "rating": "TV-14", "age_group": "Teens (13-17)",
            "duration": "2 Seasons", "seasons": 2,
            "listed_in": "International TV Shows, TV Dramas", "primary_genre": "International TV Shows", "genre_count": 2,
            "release_to_add_lag": 0.0, "is_multi_country": False, "country_count": 1
        }
    ]
    repo.insert_batch(sample_records)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    session.close()


# -----------------------------------------------------------------------------
# Health Check Tests
# -----------------------------------------------------------------------------
def test_health_endpoint(client_with_isolated_db):
    response = client_with_isolated_db.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["database_record_count"] == 2
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


# -----------------------------------------------------------------------------
# Dashboard Summary & Analytics Tests
# -----------------------------------------------------------------------------
def test_dashboard_summary_endpoint(client_with_isolated_db):
    response = client_with_isolated_db.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    assert "content" in data
    assert "temporal" in data
    assert "geographic" in data
    assert "ratings" in data
    assert "duration" in data
    assert "insights" in data
    assert data["overview"]["total_titles"] == 2


def test_analytics_overview_and_filtering(client_with_isolated_db):
    # Unfiltered
    res1 = client_with_isolated_db.get("/api/v1/analytics/overview")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total_titles"] == 2
    assert data1["movies"] == 1
    assert data1["tv_shows"] == 1

    # Filtered by content_type='Movie'
    res2 = client_with_isolated_db.get("/api/v1/analytics/overview?content_type=Movie")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_titles"] == 1
    assert data2["movies"] == 1
    assert data2["tv_shows"] == 0

    # Filtered by country='India'
    res3 = client_with_isolated_db.get("/api/v1/analytics/overview?country=India")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["total_titles"] == 1
    assert data3["tv_shows"] == 1


def test_individual_analytics_endpoints(client_with_isolated_db):
    endpoints = [
        "/api/v1/analytics/content",
        "/api/v1/analytics/temporal",
        "/api/v1/analytics/geographic",
        "/api/v1/analytics/ratings",
        "/api/v1/analytics/duration",
        "/api/v1/analytics/insights"
    ]
    for ep in endpoints:
        resp = client_with_isolated_db.get(ep)
        assert resp.status_code == 200, f"Failed for {ep}: {resp.text}"


# -----------------------------------------------------------------------------
# Content Browsing & Detail Tests
# -----------------------------------------------------------------------------
def test_content_pagination(client_with_isolated_db):
    # Page 1
    resp = client_with_isolated_db.get("/api/v1/content?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["data"]) == 1

    # Page 2
    resp2 = client_with_isolated_db.get("/api/v1/content?limit=1&offset=1")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["data"]) == 1
    assert data2["data"][0]["show_id"] != data["data"][0]["show_id"]


def test_content_detail_found(client_with_isolated_db):
    resp = client_with_isolated_db.get("/api/v1/content/api_1")
    assert resp.status_code == 200
    item = resp.json()
    assert item["show_id"] == "api_1"
    assert item["title"] == "API Film One"
    assert item["type"] == "Movie"


def test_content_detail_not_found(client_with_isolated_db):
    resp = client_with_isolated_db.get("/api/v1/content/missing_id_999")
    assert resp.status_code == 404
    error = resp.json()
    assert "Content with show_id 'missing_id_999' was not found" in error["detail"]
    assert error["error_code"] == "CONTENT_NOT_FOUND"


# -----------------------------------------------------------------------------
# Pipeline Status & Refresh Tests
# -----------------------------------------------------------------------------
def test_pipeline_status(client_with_isolated_db):
    resp = client_with_isolated_db.get("/api/v1/pipeline/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database_record_count"] == 2
    assert "configured_data_source_type" in data
    assert "configured_update_mode" in data


def test_pipeline_refresh_invalid_mode(client_with_isolated_db):
    resp = client_with_isolated_db.post(
        "/api/v1/pipeline/refresh",
        json={"mode": "invalid_unsupported_mode"}
    )
    assert resp.status_code == 400
    err = resp.json()
    assert "Invalid update mode" in err["detail"]
    assert err["error_code"] == "BAD_REQUEST"
