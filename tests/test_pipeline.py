"""
Comprehensive Unit & Integration Tests for Phase 3: ETL Pipeline.

Tests:
  - Validation: schema enforcement, fatal errors, row-level quarantine
  - Cleaning & Transformation: schema compatibility, null normalization
  - Deduplication: internal batch deduplication and database collision check
  - Pipeline Execution: first run, repeated run (idempotency), incremental updates
  - Failure Handling: missing files, empty data, corrupted rows
"""

import os
import tempfile
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.repository import NetflixRepository
from pipeline.validate_data import validate_raw_data, DataValidationError
from pipeline.clean_data import clean_dataset
from pipeline.transform_data import transform_for_database
from pipeline.deduplicate import deduplicate_records
from pipeline.load_data import load_records
from pipeline.pipeline_runner import run_pipeline


@pytest.fixture
def temp_db_session():
    """Create an isolated in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# -----------------------------------------------------------------------------
# 1. Validation Tests
# -----------------------------------------------------------------------------
def test_validation_fatal_missing_critical_column():
    """Fatal error raised when mandatory columns are completely absent."""
    bad_df = pd.DataFrame({"some_col": [1, 2, 3]})
    with pytest.raises(DataValidationError, match="Missing mandatory columns"):
        validate_raw_data(bad_df)


def test_validation_fatal_empty_dataset():
    """Fatal error raised when input DataFrame has 0 rows."""
    empty_df = pd.DataFrame(columns=["show_id", "type", "title"])
    with pytest.raises(DataValidationError, match="empty"):
        validate_raw_data(empty_df)


def test_validation_row_level_quarantine():
    """Corrupt rows (missing title, invalid type, missing show_id) are quarantined."""
    mixed_df = pd.DataFrame([
        {"show_id": "v1", "type": "Movie", "title": "Valid Movie", "release_year": 2020},
        {"show_id": "", "type": "Movie", "title": "Missing ID", "release_year": 2020},
        {"show_id": "v3", "type": "InvalidType", "title": "Bad Type", "release_year": 2020},
        {"show_id": "v4", "type": "TV Show", "title": "", "release_year": 2020},
        {"show_id": "v5", "type": "Movie", "title": "Bad Year", "release_year": "NotAYear"}
    ])
    valid_df, invalid_df, summary = validate_raw_data(mixed_df)
    assert len(valid_df) == 1
    assert valid_df.iloc[0]["show_id"] == "v1"
    assert len(invalid_df) == 4
    assert summary["invalid_records"] == 4
    assert "missing_show_id" in summary["invalid_reasons"]
    assert "invalid_type" in summary["invalid_reasons"]
    assert "missing_title" in summary["invalid_reasons"]
    assert "invalid_release_year" in summary["invalid_reasons"]


# -----------------------------------------------------------------------------
# 2. Cleaning & Transformation Integration Tests
# -----------------------------------------------------------------------------
def test_cleaning_and_transformation_pipeline():
    """Verify cleaning and feature derivation pipeline produces database-ready payload."""
    raw_sample = pd.DataFrame([{
        "show_id": "s99",
        "title": "  Sample Movie  ",
        "type": "Movie",
        "director": None,  # should be imputed
        "cast": None,      # should be imputed
        "country": "United States, Canada",
        "date_added": "January 15, 2020",
        "release_year": 2019,
        "rating": "TV-MA",
        "duration": "105 min",
        "listed_in": "Dramas, Comedies",
        "description": "Synopsis"
    }])

    # Clean
    cleaned_df, clean_sum = clean_dataset(raw_sample)
    assert cleaned_df.iloc[0]["director"] == "Unknown Director"
    assert cleaned_df.iloc[0]["primary_country"] == "United States"
    assert cleaned_df.iloc[0]["country_count"] == 2
    assert bool(cleaned_df.iloc[0]["is_multi_country"]) is True
    assert cleaned_df.iloc[0]["duration_min"] == 105.0
    assert cleaned_df.iloc[0]["age_group"] == "Adults (18+)"

    # Transform
    _, records, trans_sum = transform_for_database(cleaned_df)
    assert len(records) == 1
    rec = records[0]
    assert rec["show_id"] == "s99"
    assert rec["title"] == "Sample Movie"
    assert str(rec["date_added"]) == "2020-01-15"
    assert rec["duration_min"] == 105.0


# -----------------------------------------------------------------------------
# 3. Deduplication Tests (Level A & Level B)
# -----------------------------------------------------------------------------
def test_two_level_deduplication(temp_db_session):
    """Test both internal duplicate removal and database collision filtering."""
    repo = NetflixRepository(temp_db_session)
    # Seed DB with existing record
    repo.insert_batch([{"show_id": "existing_1", "type": "Movie", "title": "Old Movie", "release_year": 2010}])

    # Incoming batch containing:
    # 1 duplicate of existing_1 (DB collision)
    # 2 identical internal show_ids (internal dup)
    # 1 brand new unique record
    incoming = [
        {"show_id": "existing_1", "type": "Movie", "title": "Old Movie", "release_year": 2010},
        {"show_id": "new_1", "type": "Movie", "title": "Movie New", "release_year": 2021},
        {"show_id": "new_1", "type": "Movie", "title": "Movie New", "release_year": 2021},  # internal duplicate
        {"show_id": "new_2", "type": "TV Show", "title": "Series New", "release_year": 2022},
    ]

    records_to_load, summary = deduplicate_records(incoming, db_session=temp_db_session, mode="insert_new_only")
    assert summary["incoming_records"] == 4
    assert summary["internal_duplicates"] == 1
    assert summary["existing_records"] == 1
    assert summary["new_records"] == 2
    assert len(records_to_load) == 2
    ids_to_load = {r["show_id"] for r in records_to_load}
    assert ids_to_load == {"new_1", "new_2"}


# -----------------------------------------------------------------------------
# 4. Pipeline Runner End-to-End & Idempotency Tests
# -----------------------------------------------------------------------------
def test_pipeline_runner_idempotency(temp_db_session):
    """
    CRITICAL IDEMPOTENCY TEST:
    Run 1: Inserts records into empty database.
    Run 2: Re-running with same dataset results in 0 duplicates created.
    Run 3: Incremental new records insert only the new items.
    """
    # Create mini sample CSV
    sample_data = pd.DataFrame([
        {"show_id": "t1", "title": "Movie 1", "type": "Movie", "director": "D1", "cast": "A1", 
         "country": "US", "date_added": "January 1, 2020", "release_year": 2019, 
         "rating": "TV-MA", "duration": "90 min", "listed_in": "Dramas", "description": "Plot 1"},
        {"show_id": "t2", "title": "Show 2", "type": "TV Show", "director": None, "cast": "A2", 
         "country": "UK", "date_added": "February 1, 2020", "release_year": 2020, 
         "rating": "TV-14", "duration": "1 Season", "listed_in": "Comedies", "description": "Plot 2"},
    ])

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as tmp:
        sample_data.to_csv(tmp.name, index=False)
        csv_path = tmp.name

    try:
        # RUN 1: First ingestion
        report1 = run_pipeline(source_type="csv", source_path=csv_path, db_session=temp_db_session)
        assert report1["final_status"] == "SUCCESS"
        assert report1["load_summary"]["inserted"] == 2
        assert report1["final_database_total"] == 2

        # RUN 2: Re-run with EXACT same dataset (Idempotency check)
        report2 = run_pipeline(source_type="csv", source_path=csv_path, db_session=temp_db_session)
        assert report2["final_status"] == "SUCCESS"
        assert report2["load_summary"]["inserted"] == 0
        assert report2["deduplication_summary"]["existing_records"] == 2
        assert report2["final_database_total"] == 2  # Total must remain unchanged!

        # RUN 3: Incremental update with 1 new record added
        incremental_data = pd.concat([
            sample_data,
            pd.DataFrame([{"show_id": "t3", "title": "Movie 3", "type": "Movie", "director": "D3", 
                           "cast": "A3", "country": "India", "date_added": "March 1, 2020", 
                           "release_year": 2020, "rating": "PG", "duration": "120 min", 
                           "listed_in": "Action", "description": "Plot 3"}])
        ], ignore_index=True)
        incremental_data.to_csv(csv_path, index=False)

        report3 = run_pipeline(source_type="csv", source_path=csv_path, db_session=temp_db_session)
        assert report3["final_status"] == "SUCCESS"
        assert report3["load_summary"]["inserted"] == 1  # Only 1 new record inserted
        assert report3["deduplication_summary"]["existing_records"] == 2
        assert report3["final_database_total"] == 3

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


# -----------------------------------------------------------------------------
# 5. Failure Handling Tests
# -----------------------------------------------------------------------------
def test_pipeline_failure_handling_missing_file(temp_db_session):
    """Pipeline safely marks status as FAILED when data source file is missing."""
    report = run_pipeline(source_type="csv", source_path="non_existent_path_xyz.csv", db_session=temp_db_session)
    assert report["final_status"] == "FAILED"
    assert report["error_message"] is not None
    assert "not found" in report["error_message"].lower()
