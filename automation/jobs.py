"""
Scheduled and Manual Pipeline Ingestion Jobs with Concurrency Protection.
"""

import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from config.settings import (
    DATA_SOURCE_TYPE,
    DATA_SOURCE_PATH,
    DATA_UPDATE_MODE,
    SOURCE_CHANGE_DETECTION
)
from database.database import SessionLocal
from pipeline.pipeline_runner import run_pipeline
from automation.source_monitor import SourceMonitor
from automation.pipeline_monitor import PipelineMonitor

logger = logging.getLogger("PipelineAutomation")

# Concurrency lock ensuring only one pipeline execution runs at a time
_pipeline_lock = threading.Lock()
_current_running_id: Optional[str] = None


def is_pipeline_running() -> bool:
    """Check if an ETL pipeline execution is actively in progress."""
    return _pipeline_lock.locked()


def get_current_running_id() -> Optional[str]:
    """Get the run_id of the currently active pipeline execution, if any."""
    return _current_running_id if _pipeline_lock.locked() else None


def execute_pipeline_job(
    trigger_type: str = "MANUAL",
    mode: Optional[str] = None,
    source_type: Optional[str] = None,
    source_path: Optional[str] = None,
    check_source_change: bool = True,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Execute ETL pipeline with concurrency guard, change detection, and audit logging.
    
    Args:
        trigger_type: 'MANUAL' or 'SCHEDULED'
        mode: 'insert_new_only' or 'upsert'
        source_type: Source type override ('csv' or 'api')
        source_path: Source path override
        check_source_change: Whether to compare fingerprint and skip if unchanged
        db: Optional external database session
        
    Returns:
        Dict[str, Any]: Comprehensive pipeline run result.
    """
    global _current_running_id

    # 1. Attempt non-blocking lock acquisition for concurrency protection
    acquired = _pipeline_lock.acquire(blocking=False)
    if not acquired:
        logger.warning(f"Pipeline trigger rejected: another run ({_current_running_id}) is currently in progress.")
        return {
            "success": False,
            "final_status": "REJECTED",
            "error_code": "CONCURRENCY_CONFLICT",
            "message": "A pipeline execution is already in progress. Please wait for it to finish."
        }

    owns_session = db is None
    session = db or SessionLocal()
    run_id = f"pipe_{uuid.uuid4().hex[:8]}"
    _current_running_id = run_id
    start_time = datetime.now(timezone.utc)

    effective_mode = (mode or DATA_UPDATE_MODE).lower()
    effective_stype = (source_type or DATA_SOURCE_TYPE).lower()
    effective_spath = source_path or DATA_SOURCE_PATH

    try:
        # 2. Compute Source Fingerprint
        fingerprint = SourceMonitor.compute_source_fingerprint(
            source_type=effective_stype,
            source_path=effective_spath
        )

        # Check if source file/endpoint is unavailable
        if not fingerprint.get("exists", False):
            err = fingerprint.get("error", "Source unavailable")
            PipelineMonitor.start_run(
                db=session,
                run_id=run_id,
                trigger_type=trigger_type,
                update_mode=effective_mode,
                source_type=effective_stype,
                source_identifier=effective_spath,
                source_fingerprint=None
            )
            PipelineMonitor.finish_run(
                db=session,
                run_id=run_id,
                status="FAILED",
                duration_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
                error_message=err
            )
            return {
                "success": False,
                "final_status": "FAILED",
                "run_id": run_id,
                "error_message": err
            }

        # 3. Source Change Detection
        if check_source_change:
            changed, prev_state, reason = SourceMonitor.has_source_changed(session, fingerprint)
            if not changed:
                logger.info(f"Pipeline [{run_id}]: {reason}. Skipping ETL run.")
                PipelineMonitor.record_skipped_run(
                    db=session,
                    run_id=run_id,
                    trigger_type=trigger_type,
                    update_mode=effective_mode,
                    source_type=effective_stype,
                    source_identifier=effective_spath,
                    reason=reason,
                    source_fingerprint=fingerprint["checksum"]
                )
                return {
                    "success": True,
                    "final_status": "SKIPPED",
                    "run_id": run_id,
                    "message": reason,
                    "duration_seconds": 0.0,
                    "incremental_metrics": {
                        "incoming_records": 0,
                        "internal_duplicates": 0,
                        "existing_records": fingerprint.get("row_count", 0),
                        "new_records": 0,
                        "inserted": 0,
                        "updated": 0,
                        "skipped": 0,
                        "failed": 0,
                        "mode": effective_mode
                    }
                }

        # 4. Source Changed (or forced): Record RUNNING
        PipelineMonitor.start_run(
            db=session,
            run_id=run_id,
            trigger_type=trigger_type,
            update_mode=effective_mode,
            source_type=effective_stype,
            source_identifier=effective_spath,
            source_fingerprint=fingerprint["checksum"]
        )

        # 5. Execute ETL Pipeline
        logger.info(f"Triggering ETL Pipeline [{run_id}] (trigger={trigger_type}, mode={effective_mode})...")
        report = run_pipeline(
            source_type=effective_stype,
            source_path=effective_spath,
            mode=effective_mode,
            db_session=session
        )

        status = report.get("final_status", "FAILED")
        duration = report.get("duration_seconds", 0.0)
        metrics = report.get("incremental_metrics", {})
        error_msg = report.get("error_message")

        # 6. If Successful or Partial: Update Source State
        if status in ["SUCCESS", "PARTIAL_SUCCESS"]:
            SourceMonitor.record_successful_source_state(session, fingerprint)

        # 7. Update Audit Ledger Entry
        PipelineMonitor.finish_run(
            db=session,
            run_id=run_id,
            status=status,
            duration_seconds=duration,
            metrics=metrics,
            error_message=error_msg
        )

        report["success"] = (status in ["SUCCESS", "PARTIAL_SUCCESS"])
        report["run_id"] = run_id
        return report

    except Exception as e:
        logger.error(f"Execution failed for job [{run_id}]: {e}", exc_info=True)
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        PipelineMonitor.finish_run(
            db=session,
            run_id=run_id,
            status="FAILED",
            duration_seconds=duration,
            error_message=str(e)
        )
        return {
            "success": False,
            "final_status": "FAILED",
            "run_id": run_id,
            "error_message": str(e)
        }

    finally:
        _current_running_id = None
        _pipeline_lock.release()
        if owns_session:
            session.close()


def scheduled_refresh_job():
    """Scheduled task entrypoint invoked periodically by APScheduler."""
    logger.info("APScheduler: Executing scheduled catalog refresh job...")
    return execute_pipeline_job(
        trigger_type="SCHEDULED",
        mode=DATA_UPDATE_MODE,
        check_source_change=SOURCE_CHANGE_DETECTION
    )
