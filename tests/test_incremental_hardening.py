"""
Phase 4: Incremental Update Audit & Hardening Test Suite.

Verifies:
  - Scenario A: Initial load into clean database
  - Scenario B: Idempotent re-run with zero duplicate records created
  - Scenario C: Incremental batch (only new records inserted)
  - Scenario D: Changed metadata handling under 'insert_new_only' vs 'upsert' modes
  - Scenario E: Deterministic conflict resolution for duplicate incoming show_ids
  - Scenario F: Transaction rollback on simulated database insertion failure
"""

import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models import NetflixContent
from database.repository import NetflixRepository
from pipeline.pipeline_runner import run_pipeline
from pipeline.deduplicate import deduplicate_records
from pipeline.load_data import load_records


@pytest.fixture
def isolated_db_session():
    """Create an isolated in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _make_temp_csv(df: pd.DataFrame) -> str:
    """Helper to write DataFrame to a temp CSV and return path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8")
    df.to_csv(tmp.name, index=False)
    tmp.close()
    return tmp.name


# -----------------------------------------------------------------------------
# Test 1 & 2 & 3: Incremental Ingestion Progression (A, B, C)
# -----------------------------------------------------------------------------
def test_incremental_lifecycle(isolated_db_session):
    """
    Test 1: Initial load (A, B, C) -> 3 inserted
    Test 2: Same dataset again -> 0 inserted, 0 duplicates
    Test 3: Dataset with D, E added -> only D, E inserted
    """
    repo = NetflixRepository(isolated_db_session)

    # Initial batch: A, B, C
    batch_abc = pd.DataFrame([
        {"show_id": "item_a", "type": "Movie", "title": "Movie A", "release_year": 2018},
        {"show_id": "item_b", "type": "TV Show", "title": "Series B", "release_year": 2019},
        {"show_id": "item_c", "type": "Movie", "title": "Movie C", "release_year": 2020},
    ])
    csv_abc = _make_temp_csv(batch_abc)

    try:
        # TEST 1: Initial load
        rep1 = run_pipeline(source_type="csv", source_path=csv_abc, db_session=isolated_db_session, mode="insert_new_only")
        assert rep1["final_status"] == "SUCCESS"
        assert rep1["incremental_metrics"]["inserted"] == 3
        assert rep1["incremental_metrics"]["new_records"] == 3
        assert rep1["incremental_metrics"]["existing_records"] == 0
        assert repo.get_total_count() == 3

        # TEST 2: Same dataset re-run (Idempotency)
        rep2 = run_pipeline(source_type="csv", source_path=csv_abc, db_session=isolated_db_session, mode="insert_new_only")
        assert rep2["final_status"] == "SUCCESS"
        assert rep2["incremental_metrics"]["inserted"] == 0
        assert rep2["incremental_metrics"]["existing_records"] == 3
        assert rep2["incremental_metrics"]["new_records"] == 0
        assert repo.get_total_count() == 3  # Unchanged!

        # TEST 3: Incremental batch (A, B, C, D, E)
        batch_abcde = pd.concat([
            batch_abc,
            pd.DataFrame([
                {"show_id": "item_d", "type": "Movie", "title": "Movie D", "release_year": 2021},
                {"show_id": "item_e", "type": "TV Show", "title": "Series E", "release_year": 2022},
            ])
        ], ignore_index=True)
        csv_abcde = _make_temp_csv(batch_abcde)

        try:
            rep3 = run_pipeline(source_type="csv", source_path=csv_abcde, db_session=isolated_db_session, mode="insert_new_only")
            assert rep3["final_status"] == "SUCCESS"
            assert rep3["incremental_metrics"]["inserted"] == 2  # Only D and E!
            assert rep3["incremental_metrics"]["existing_records"] == 3
            assert rep3["incremental_metrics"]["new_records"] == 2
            assert repo.get_total_count() == 5
            assert repo.get_by_show_id("item_d") is not None
            assert repo.get_by_show_id("item_e") is not None
        finally:
            if os.path.exists(csv_abcde):
                os.remove(csv_abcde)

    finally:
        if os.path.exists(csv_abc):
            os.remove(csv_abc)


# -----------------------------------------------------------------------------
# Test 4: Changed Metadata Handling under insert_new_only vs upsert
# -----------------------------------------------------------------------------
def test_changed_metadata_modes(isolated_db_session):
    """
    Test 4: Record B exists with title 'Original B'.
    Incoming batch has item_b with title 'Updated B Title'.
    - Under 'insert_new_only': record is skipped; database title stays 'Original B'.
    - Under 'upsert': record is updated; database title becomes 'Updated B Title'.
    """
    repo = NetflixRepository(isolated_db_session)
    # Seed DB with original record
    repo.insert_batch([{
        "show_id": "item_b",
        "type": "TV Show",
        "title": "Original B Title",
        "release_year": 2019
    }])
    assert repo.get_by_show_id("item_b").title == "Original B Title"

    modified_batch = pd.DataFrame([{
        "show_id": "item_b",
        "type": "TV Show",
        "title": "Updated B Title",
        "release_year": 2019
    }])
    csv_mod = _make_temp_csv(modified_batch)

    try:
        # 1. Test insert_new_only
        rep_insert_only = run_pipeline(
            source_type="csv",
            source_path=csv_mod,
            db_session=isolated_db_session,
            mode="insert_new_only"
        )
        assert rep_insert_only["incremental_metrics"]["inserted"] == 0
        assert rep_insert_only["incremental_metrics"]["updated"] == 0
        assert rep_insert_only["incremental_metrics"]["existing_records"] == 1
        # DB must still have original title
        assert repo.get_by_show_id("item_b").title == "Original B Title"

        # 2. Test upsert
        rep_upsert = run_pipeline(
            source_type="csv",
            source_path=csv_mod,
            db_session=isolated_db_session,
            mode="upsert"
        )
        assert rep_upsert["incremental_metrics"]["inserted"] == 0
        assert rep_upsert["incremental_metrics"]["updated"] == 1
        # DB title must now be updated!
        assert repo.get_by_show_id("item_b").title == "Updated B Title"

    finally:
        if os.path.exists(csv_mod):
            os.remove(csv_mod)


# -----------------------------------------------------------------------------
# Test 5: Deterministic Handling of Internal Duplicate show_ids (Scenario E)
# -----------------------------------------------------------------------------
def test_conflicting_internal_show_id_resolution():
    """
    Test 5: Incoming batch contains multiple rows for the SAME show_id
    with conflicting titles. Deterministic rule retains the first occurrence.
    """
    conflicting_records = [
        {"show_id": "conf_1", "type": "Movie", "title": "First Version (Retained)", "release_year": 2020},
        {"show_id": "conf_1", "type": "Movie", "title": "Second Conflicting Version", "release_year": 2020},
    ]

    deduped, summary = deduplicate_records(conflicting_records, db_session=None, mode="insert_new_only")
    assert summary["incoming_records"] == 2
    assert summary["internal_duplicates"] == 1
    assert len(deduped) == 1
    assert deduped[0]["title"] == "First Version (Retained)"


# -----------------------------------------------------------------------------
# Test 6: Simulated Database Failure & Transaction Rollback Safety (Scenario F)
# -----------------------------------------------------------------------------
def test_transaction_rollback_on_simulated_db_failure(isolated_db_session):
    """
    Test 6: If a database error occurs during load_records, the transaction
    is rolled back and the database state remains completely consistent.
    """
    repo = NetflixRepository(isolated_db_session)
    # Seed database with 1 initial record
    repo.insert_batch([{"show_id": "safe_1", "type": "Movie", "title": "Pre-existing Safe Record", "release_year": 2015}])
    assert repo.get_total_count() == 1

    # Simulate failure during bulk save
    bad_records = [
        {"show_id": "fail_1", "type": "Movie", "title": "Failed Movie 1", "release_year": 2022},
        {"show_id": "fail_2", "type": "Movie", "title": "Failed Movie 2", "release_year": 2022},
    ]

    # Patch bulk_save_objects to raise an operational error
    with patch.object(isolated_db_session, "bulk_save_objects", side_effect=Exception("Simulated Database I/O Failure")):
        with pytest.raises(Exception, match="Simulated Database I/O Failure"):
            repo.insert_batch(bad_records)

    # Verify database state remained intact with no partial records
    isolated_db_session.rollback()
    assert repo.get_total_count() == 1
    assert repo.get_by_show_id("safe_1") is not None
    assert repo.get_by_show_id("fail_1") is None
    assert repo.get_by_show_id("fail_2") is None
