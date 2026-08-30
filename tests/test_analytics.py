"""
Unit & Integration Tests for Phase 5: Analytics Engine (analytics/).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.repository import NetflixRepository
from analytics.analytics_service import AnalyticsService


@pytest.fixture
def analytics_test_db():
    """Create an isolated in-memory SQLite database populated with controlled sample data."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    repo = NetflixRepository(session)
    sample_records = [
        {
            "show_id": "a1", "type": "Movie", "title": "Film One", "release_year": 2018,
            "year_added": 2019, "month_added": 1, "month_name_added": "January",
            "country": "United States, Canada", "primary_country": "United States",
            "is_multi_country": True, "country_count": 2, "rating": "TV-MA", "age_group": "Adults (18+)",
            "duration": "90 min", "duration_min": 90.0, "movie_duration_tier": "60-90 min (Standard)",
            "listed_in": "Dramas, Comedies", "primary_genre": "Dramas", "genre_count": 2,
            "release_to_add_lag": 1.0
        },
        {
            "show_id": "a2", "type": "Movie", "title": "Film Two", "release_year": 2020,
            "year_added": 2020, "month_added": 10, "month_name_added": "October",
            "country": "India", "primary_country": "India",
            "is_multi_country": False, "country_count": 1, "rating": "TV-14", "age_group": "Teens (13-17)",
            "duration": "120 min", "duration_min": 120.0, "movie_duration_tier": "90-120 min (Feature)",
            "listed_in": "Comedies", "primary_genre": "Comedies", "genre_count": 1,
            "release_to_add_lag": 0.0
        },
        {
            "show_id": "a3", "type": "TV Show", "title": "Series Three", "release_year": 2015,
            "year_added": 2018, "month_added": 1, "month_name_added": "January",
            "country": "United Kingdom", "primary_country": "United Kingdom",
            "is_multi_country": False, "country_count": 1, "rating": "TV-MA", "age_group": "Adults (18+)",
            "duration": "3 Seasons", "seasons": 3,
            "listed_in": "British TV Shows, Dramas", "primary_genre": "British TV Shows", "genre_count": 2,
            "release_to_add_lag": 3.0
        },
        {
            "show_id": "a4", "type": "TV Show", "title": "Series Four", "release_year": 2021,
            "year_added": 2021, "month_added": 11, "month_name_added": "November",
            "country": "South Korea", "primary_country": "South Korea",
            "is_multi_country": False, "country_count": 1, "rating": "TV-14", "age_group": "Teens (13-17)",
            "duration": "1 Season", "seasons": 1,
            "listed_in": "International TV Shows", "primary_genre": "International TV Shows", "genre_count": 1,
            "release_to_add_lag": 0.0
        }
    ]
    repo.insert_batch(sample_records)

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def empty_db_session():
    """Create an empty in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_overview_metrics(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    ov = service.get_overview()

    assert ov["total_titles"] == 4
    assert ov["movies"] == 2
    assert ov["tv_shows"] == 2
    assert ov["movie_percentage"] == 50.0
    assert ov["tv_show_percentage"] == 50.0
    assert ov["earliest_release_year"] == 2015
    assert ov["latest_release_year"] == 2021
    assert ov["total_countries"] == 4


def test_content_type_analysis(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    res = service.get_content_analysis()

    assert "Movie" in res["content_type"]["labels"]
    assert "TV Show" in res["content_type"]["labels"]
    assert res["multi_genre_percentage"] == 50.0
    assert "Dramas" in res["top_genres_overall"]["labels"]


def test_temporal_analysis(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    res = service.get_temporal_analysis()

    assert 2018 in res["yearly_additions"]["years"]
    assert 2019 in res["yearly_additions"]["years"]
    assert "January" in res["monthly_seasonality"]["months"]
    assert res["licensing_lag_stats"]["median_lag_years"] >= 0.0


def test_geographic_analysis(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    res = service.get_geographic_analysis()

    assert "United States" in res["top_countries_all_credits"]["labels"]
    assert res["co_production_count"] == 1
    assert res["co_production_percentage"] == 25.0


def test_rating_analysis(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    res = service.get_rating_analysis()

    assert "TV-MA" in res["ratings"]["labels"]
    assert "Adults (18+)" in res["age_groups"]["labels"]
    assert res["dominant_rating"] in ["TV-MA", "TV-14"]


def test_duration_analysis(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    res = service.get_duration_analysis()

    movies = res["movies"]
    assert movies["count"] == 2
    assert movies["mean_min"] == 105.0
    assert movies["min_min"] == 90.0
    assert movies["max_min"] == 120.0

    tv = res["tv_shows"]
    assert tv["count"] == 2
    assert tv["single_season_pct"] == 50.0
    assert tv["max_seasons"] == 3


def test_analytics_filtering(analytics_test_db):
    service = AnalyticsService(analytics_test_db)

    # Filter by content_type = 'Movie'
    movie_ov = service.get_overview(filters={"content_type": "Movie"})
    assert movie_ov["total_titles"] == 2
    assert movie_ov["movies"] == 2
    assert movie_ov["tv_shows"] == 0

    # Filter by min_year = 2020
    year_ov = service.get_overview(filters={"release_year_min": 2020})
    assert year_ov["total_titles"] == 2

    # Filter by country = 'India'
    india_ov = service.get_overview(filters={"country": "India"})
    assert india_ov["total_titles"] == 1


def test_insights_generation(analytics_test_db):
    service = AnalyticsService(analytics_test_db)
    insights = service.get_all_insights()

    assert len(insights) >= 5
    categories = [ins["category"] for ins in insights]
    assert "content_mix" in categories
    assert "geographic_dominance" in categories
    assert "genre_popularity" in categories


def test_empty_database_safety(empty_db_session):
    service = AnalyticsService(empty_db_session)

    ov = service.get_overview()
    assert ov["total_titles"] == 0
    assert ov["movie_percentage"] == 0.0

    content = service.get_content_analysis()
    assert content["total_unique_genres"] == 0

    geo = service.get_geographic_analysis()
    assert geo["co_production_count"] == 0

    dur = service.get_duration_analysis()
    assert dur["movies"]["count"] == 0
    assert dur["tv_shows"]["count"] == 0

    insights = service.get_all_insights()
    assert len(insights) >= 1
    assert insights[0]["category"] == "catalog_status"
