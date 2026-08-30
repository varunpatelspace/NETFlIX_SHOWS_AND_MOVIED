"""
Comprehensive Unit Tests for Phase 8: Automated Data Refresh, Scheduling,
Source Change Detection, Pipeline Monitoring, and Concurrency Protection.
"""

import os
import tempfile
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database.database import Base, get_db
from database.models import PipelineRun, SourceState, NetflixContent
from automation.source_monitor import SourceMonitor
from automation.pipeline_monitor import PipelineMonitor
from automation.jobs import execute_pipeline_job, _pipeline_lock
from automation.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from api.main import app


# -----------------------------------------------------------------------------
# Test Fixtures: In-Memory SQLite Database
# -----------------------------------------------------------------------------
@pytest.fixture
def in_memory_db():
    """Create a thread-safe in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session, engine
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# -----------------------------------------------------------------------------
# 1. Source Monitor Tests
# -----------------------------------------------------------------------------
def test_source_monitor_first_fingerprint_and_unchanged(in_memory_db):
    session, engine = in_memory_db

    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("show_id,title,type,release_year,rating,duration,listed_in,description\n")
        f.write("s1001,Test Film,Movie,2020,PG-13,95 min,Dramas,Test Description\n")
        tmp_path = f.name

    try:
        # First fingerprint
        fp1 = SourceMonitor.compute_source_fingerprint(source_type="csv", source_path=tmp_path)
        assert fp1["exists"] is True
        assert fp1["row_count"] == 1
        assert len(fp1["checksum"]) == 64

        # First change check -> should report changed because no previous state exists
        changed, prev, reason = SourceMonitor.has_source_changed(session, fp1)
        assert changed is True
        assert prev is None
        assert "Initial execution" in reason

        # Record successful source state
        saved_state = SourceMonitor.record_successful_source_state(session, fp1)
        assert saved_state.fingerprint == fp1["fingerprint"]
        assert saved_state.checksum == fp1["checksum"]

        # Check again without modifying the file -> should be unchanged
        changed2, prev2, reason2 = SourceMonitor.has_source_changed(session, fp1)
        assert changed2 is False
        assert prev2 is not None
        assert "unchanged" in reason2.lower()

        # Modify the file (append a new row)
        with open(tmp_path, "a") as f:
            f.write("s1002,Test Film 2,Movie,2021,R,110 min,Comedies,Test 2\n")

        fp2 = SourceMonitor.compute_source_fingerprint(source_type="csv", source_path=tmp_path)
        assert fp2["row_count"] == 2
        assert fp2["checksum"] != fp1["checksum"]

        # Check again -> should report changed
        changed3, prev3, reason3 = SourceMonitor.has_source_changed(session, fp2)
        assert changed3 is True
        assert "Source changed" in reason3

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_source_monitor_missing_source():
    fp = SourceMonitor.compute_source_fingerprint(source_type="csv", source_path="non_existent_file_xyz.csv")
    assert fp["exists"] is False
    assert "not found" in fp["error"]


# -----------------------------------------------------------------------------
# 2. Pipeline Monitor & Audit Ledger Tests
# -----------------------------------------------------------------------------
def test_pipeline_monitor_lifecycle(in_memory_db):
    session, _ = in_memory_db

    # 1. Start run
    run = PipelineMonitor.start_run(
        db=session,
        run_id="pipe_test01",
        trigger_type="MANUAL",
        update_mode="insert_new_only",
        source_type="csv",
        source_identifier="data/test.csv",
        source_fingerprint="abc123hash"
    )
    assert run.status == "RUNNING"
    assert run.started_at is not None

    # 2. Finish run with metrics
    metrics = {
        "incoming_records": 10,
        "internal_duplicates": 1,
        "existing_records": 0,
        "new_records": 9,
        "inserted": 9,
        "updated": 0,
        "skipped": 0,
        "failed": 0
    }
    finished = PipelineMonitor.finish_run(
        db=session,
        run_id="pipe_test01",
        status="SUCCESS",
        duration_seconds=1.234,
        metrics=metrics
    )
    assert finished.status == "SUCCESS"
    assert finished.inserted == 9
    assert finished.execution_duration == 1.234
    assert finished.completed_at is not None

    # 3. Record skipped run
    skipped = PipelineMonitor.record_skipped_run(
        db=session,
        run_id="pipe_test02",
        trigger_type="SCHEDULED",
        update_mode="insert_new_only",
        reason="Source unchanged"
    )
    assert skipped.status == "SKIPPED"
    assert skipped.trigger_type == "SCHEDULED"
    assert skipped.execution_duration == 0.0

    # 4. History retrieval
    total, history = PipelineMonitor.get_history(session, limit=10)
    assert total == 2
    assert len(history) == 2

    # Filter history by status
    total_skipped, skipped_runs = PipelineMonitor.get_history(session, status_filter="SKIPPED")
    assert total_skipped == 1
    assert skipped_runs[0].run_id == "pipe_test02"

    # Get by ID
    fetched = PipelineMonitor.get_run_by_id(session, "pipe_test01")
    assert fetched is not None
    assert fetched.run_id == "pipe_test01"


# -----------------------------------------------------------------------------
# 3. Concurrency Protection Tests
# -----------------------------------------------------------------------------
def test_concurrency_protection(in_memory_db):
    session, _ = in_memory_db

    # Acquire the lock to simulate an active running pipeline
    assert _pipeline_lock.acquire(blocking=False) is True

    try:
        # Attempt to run another pipeline execution while lock is held
        res = execute_pipeline_job(
            trigger_type="MANUAL",
            db=session
        )
        assert res["success"] is False
        assert res["final_status"] == "REJECTED"
        assert res["error_code"] == "CONCURRENCY_CONFLICT"
    finally:
        _pipeline_lock.release()

    # Now that the lock is released, lock can be acquired again
    assert _pipeline_lock.locked() is False


# -----------------------------------------------------------------------------
# 4. Persistence Across Database Sessions
# -----------------------------------------------------------------------------
def test_persistence_across_sessions(in_memory_db):
    session, engine = in_memory_db
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Session 1: Create a run and source state
    s1 = TestingSession()
    r = PipelineMonitor.start_run(s1, "pipe_persist_01", "SCHEDULED", "upsert")
    PipelineMonitor.finish_run(s1, "pipe_persist_01", "SUCCESS", 2.5, metrics={"inserted": 5})
    s1.close()

    # Session 2: Read it back
    s2 = TestingSession()
    run = PipelineMonitor.get_run_by_id(s2, "pipe_persist_01")
    assert run is not None
    assert run.status == "SUCCESS"
    assert run.inserted == 5
    assert run.execution_duration == 2.5
    s2.close()


# -----------------------------------------------------------------------------
# 5. API Endpoints for Automation and History
# -----------------------------------------------------------------------------
def test_api_automation_endpoints(in_memory_db):
    session, _ = in_memory_db

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # Add a run to history
        PipelineMonitor.record_skipped_run(session, "pipe_api_test", "SCHEDULED", "insert_new_only")

        # 1. GET /api/v1/automation/status
        resp_auto = client.get("/api/v1/automation/status")
        assert resp_auto.status_code == 200
        data_auto = resp_auto.json()
        assert "scheduler_enabled" in data_auto
        assert "scheduler_running" in data_auto
        assert "update_frequency_seconds" in data_auto

        # 2. GET /api/v1/pipeline/history
        resp_hist = client.get("/api/v1/pipeline/history?limit=10")
        assert resp_hist.status_code == 200
        data_hist = resp_hist.json()
        assert data_hist["total"] >= 1
        assert len(data_hist["data"]) >= 1
        assert data_hist["data"][0]["run_id"] == "pipe_api_test"

        # 3. GET /api/v1/pipeline/history/{run_id}
        resp_detail = client.get("/api/v1/pipeline/history/pipe_api_test")
        assert resp_detail.status_code == 200
        detail = resp_detail.json()
        assert detail["run_id"] == "pipe_api_test"
        assert detail["status"] == "SKIPPED"

        # 4. GET /api/v1/pipeline/history/non_existent_run
        resp_404 = client.get("/api/v1/pipeline/history/non_existent_run")
        assert resp_404.status_code == 404
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 6. Scheduler Initialization & Disabled Mode Tests
# -----------------------------------------------------------------------------
def test_scheduler_initialization_and_disabled_mode(monkeypatch):
    # Test disabled mode
    monkeypatch.setattr("automation.scheduler.ENABLE_SCHEDULER", False)
    started = start_scheduler()
    assert started is False

    status = get_scheduler_status()
    assert status["scheduler_enabled"] is False
    assert status["scheduler_running"] is False
