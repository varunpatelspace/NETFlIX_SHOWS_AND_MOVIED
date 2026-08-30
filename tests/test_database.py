"""
Unit Tests for Database Layer (database/database.py, models.py, repository.py).
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models import NetflixContent
from database.repository import NetflixRepository


@pytest.fixture
def test_db_session():
    """Create an in-memory SQLite database for isolated test execution."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_insert_and_query_record(test_db_session):
    repo = NetflixRepository(test_db_session)

    sample_records = [
        {
            "show_id": "s1",
            "type": "Movie",
            "title": "Test Movie 1",
            "director": "Director One",
            "cast": "Actor A, Actor B",
            "country": "United States",
            "date_added": "2020-01-15",
            "release_year": 2019,
            "rating": "TV-MA",
            "duration": "95 min",
            "listed_in": "Dramas, International Movies",
            "description": "Test movie description.",
            "year_added": 2020,
            "month_added": 1,
            "month_name_added": "January",
            "day_added": 15,
            "duration_min": 95.0,
            "age_group": "Adults (18+)",
            "primary_country": "United States",
            "primary_genre": "Dramas",
            "has_director_info": True,
            "has_cast_info": True,
            "has_country_info": True,
            "has_date_added": True
        },
        {
            "show_id": "s2",
            "type": "TV Show",
            "title": "Test TV Show 1",
            "director": "Unknown Director",
            "cast": "Actor C",
            "country": "South Korea",
            "date_added": "2021-03-10",
            "release_year": 2021,
            "rating": "TV-14",
            "duration": "2 Seasons",
            "listed_in": "International TV Shows, Romantic TV Shows",
            "description": "Test series description.",
            "year_added": 2021,
            "month_added": 3,
            "month_name_added": "March",
            "day_added": 10,
            "seasons": 2,
            "age_group": "Teens (13-17)",
            "primary_country": "South Korea",
            "primary_genre": "International TV Shows",
            "has_director_info": False,
            "has_cast_info": True,
            "has_country_info": True,
            "has_date_added": True
        }
    ]

    inserted = repo.insert_batch(sample_records)
    assert inserted == 2
    assert repo.get_total_count() == 2

    # Check query by id
    item = repo.get_by_show_id("s1")
    assert item is not None
    assert item.title == "Test Movie 1"
    assert item.duration_min == 95.0

    # Check type counts
    type_counts = repo.get_type_counts()
    assert type_counts["Movie"] == 1
    assert type_counts["TV Show"] == 1

    # Check existing IDs
    existing_ids = repo.get_existing_show_ids()
    assert "s1" in existing_ids
    assert "s2" in existing_ids
    assert "s3" not in existing_ids


def test_upsert_logic(test_db_session):
    repo = NetflixRepository(test_db_session)

    initial_record = [{
        "show_id": "s10",
        "type": "Movie",
        "title": "Old Title",
        "release_year": 2018
    }]
    repo.insert_batch(initial_record)
    assert repo.get_by_show_id("s10").title == "Old Title"

    update_records = [
        {
            "show_id": "s10",
            "type": "Movie",
            "title": "Updated Title",
            "release_year": 2018
        },
        {
            "show_id": "s11",
            "type": "TV Show",
            "title": "Brand New Show",
            "release_year": 2022
        }
    ]
    res = repo.upsert_batch(update_records)
    assert res["updated"] == 1
    assert res["inserted"] == 1
    assert repo.get_total_count() == 2
    assert repo.get_by_show_id("s10").title == "Updated Title"
    assert repo.get_by_show_id("s11").title == "Brand New Show"


def test_dataframe_retrieval(test_db_session):
    repo = NetflixRepository(test_db_session)
    records = [
        {
            "show_id": "s20",
            "type": "Movie",
            "title": "Movie A",
            "country": "India",
            "primary_country": "India",
            "listed_in": "Comedies",
            "primary_genre": "Comedies",
            "release_year": 2015
        },
        {
            "show_id": "s21",
            "type": "TV Show",
            "title": "Show B",
            "country": "United States",
            "primary_country": "United States",
            "listed_in": "Dramas",
            "primary_genre": "Dramas",
            "release_year": 2020
        }
    ]
    repo.insert_batch(records)

    # Full df
    df = repo.get_dataframe()
    assert len(df) == 2
    assert "show_id" in df.columns

    # Filter by content_type
    movie_df = repo.get_dataframe(content_type="Movie")
    assert len(movie_df) == 1
    assert movie_df.iloc[0]["title"] == "Movie A"

    # Filter by year
    year_df = repo.get_dataframe(min_year=2018)
    assert len(year_df) == 1
    assert year_df.iloc[0]["title"] == "Show B"
