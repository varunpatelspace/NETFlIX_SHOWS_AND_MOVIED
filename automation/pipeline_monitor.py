"""
Pipeline Execution Audit and Run Lifecycle Monitor.

Tracks every ETL execution (manual and scheduled), recording detailed operational
metrics, durations, trigger types, and status outcomes in the database ledger.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import PipelineRun


class PipelineMonitor:
    """
    Manages persistent pipeline execution records and operational history.
    """

    @staticmethod
    def start_run(
        db: Session,
        run_id: str,
        trigger_type: str,
        update_mode: str,
        source_type: Optional[str] = None,
        source_identifier: Optional[str] = None,
        source_fingerprint: Optional[str] = None
    ) -> PipelineRun:
        """Create and persist a new pipeline run entry in RUNNING state."""
        run = PipelineRun(
            run_id=run_id,
            started_at=datetime.now(timezone.utc),
            status="RUNNING",
            trigger_type=trigger_type.upper(),
            update_mode=update_mode.lower(),
            source_type=source_type,
            source_identifier=source_identifier,
            source_fingerprint=source_fingerprint
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def finish_run(
        db: Session,
        run_id: str,
        status: str,
        duration_seconds: float,
        metrics: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[PipelineRun]:
        """Update an existing pipeline run with terminal execution metrics."""
        run = db.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
        if not run:
            return None

        m = metrics or {}
        run.completed_at = datetime.now(timezone.utc)
        run.status = status.upper()
        run.execution_duration = round(duration_seconds, 4)
        run.error_message = error_message

        # Populate structured ingestion counts
        run.incoming_records = m.get("incoming_records", 0)
        run.internal_duplicates = m.get("internal_duplicates", 0)
        run.existing_records = m.get("existing_records", 0)
        run.new_records = m.get("new_records", 0)
        run.inserted = m.get("inserted", 0)
        run.updated = m.get("updated", 0)
        run.skipped = m.get("skipped", 0)
        run.failed = m.get("failed", 0)

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def record_skipped_run(
        db: Session,
        run_id: str,
        trigger_type: str,
        update_mode: str,
        source_type: Optional[str] = None,
        source_identifier: Optional[str] = None,
        reason: str = "Source unchanged since previous successful refresh",
        source_fingerprint: Optional[str] = None
    ) -> PipelineRun:
        """Create and immediately complete a SKIPPED pipeline run entry."""
        now = datetime.now(timezone.utc)
        run = PipelineRun(
            run_id=run_id,
            started_at=now,
            completed_at=now,
            status="SKIPPED",
            trigger_type=trigger_type.upper(),
            update_mode=update_mode.lower(),
            source_type=source_type,
            source_identifier=source_identifier,
            source_fingerprint=source_fingerprint,
            execution_duration=0.0,
            error_message=reason
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_history(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> Tuple[int, List[PipelineRun]]:
        """Retrieve paginated pipeline history records."""
        query = db.query(PipelineRun)
        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(PipelineRun.status == status_filter.upper())

        total = query.count()
        records = query.order_by(desc(PipelineRun.id)).offset(offset).limit(limit).all()
        return total, records

    @staticmethod
    def get_run_by_id(db: Session, run_id: str) -> Optional[PipelineRun]:
        """Fetch full details for a specific pipeline execution."""
        return db.query(PipelineRun).filter(
            (PipelineRun.run_id == run_id) | (PipelineRun.id == int(run_id) if run_id.isdigit() else False)
        ).first()

    @staticmethod
    def get_last_run(db: Session) -> Optional[PipelineRun]:
        """Fetch the most recent pipeline run regardless of status."""
        return db.query(PipelineRun).order_by(desc(PipelineRun.id)).first()

    @staticmethod
    def get_last_successful_run(db: Session) -> Optional[PipelineRun]:
        """Fetch the most recent run with status SUCCESS or PARTIAL_SUCCESS."""
        return db.query(PipelineRun).filter(
            PipelineRun.status.in_(["SUCCESS", "PARTIAL_SUCCESS"])
        ).order_by(desc(PipelineRun.id)).first()
