from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from config.settings import DATA_SOURCE_TYPE, DATA_SOURCE_PATH, DATA_UPDATE_MODE
from database.database import get_db
from database.repository import NetflixRepository
from api.dependencies import get_repository
from api.schemas.pipeline import PipelineRefreshRequest, PipelineStatusResponse
from automation.jobs import execute_pipeline_job
from automation.pipeline_monitor import PipelineMonitor
from automation.scheduler import get_scheduler_status

router = APIRouter(prefix="/api/v1", tags=["Pipeline & Automation"])


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusResponse,
    summary="Data Pipeline & Ingestion Status",
    description="Retrieve current database state, record count, latest update timestamp, and configured ingestion settings."
)
def get_pipeline_status(repo: NetflixRepository = Depends(get_repository)):
    """Fetch current pipeline and database configuration status."""
    total_count = repo.get_total_count()
    latest_ts = repo.get_latest_timestamp()

    return PipelineStatusResponse(
        status="ready",
        database_record_count=total_count,
        latest_database_update_timestamp=latest_ts,
        configured_data_source_type=DATA_SOURCE_TYPE,
        configured_data_source_path=DATA_SOURCE_PATH,
        configured_update_mode=DATA_UPDATE_MODE,
        historical_pipeline_records="Current system status only"
    )


@router.post(
    "/pipeline/refresh",
    summary="Trigger On-Demand Data Ingestion",
    description="Execute the automated ETL pipeline with configurable update mode ('insert_new_only' or 'upsert') and concurrency guard."
)
def trigger_pipeline_refresh(
    request: PipelineRefreshRequest = PipelineRefreshRequest(),
    db: Session = Depends(get_db)
):
    """Execute end-to-end data ingestion pipeline with audit logging and concurrency protection."""
    valid_modes = ["insert_new_only", "upsert"]
    mode = (request.mode or DATA_UPDATE_MODE).lower()

    if mode not in valid_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid update mode '{request.mode}'. Supported modes are: {valid_modes}"
        )

    report = execute_pipeline_job(
        trigger_type="MANUAL",
        mode=mode,
        source_type=request.source_type,
        source_path=request.source_path,
        check_source_change=False,  # Manual refresh forces execution
        db=db
    )

    if report.get("error_code") == "CONCURRENCY_CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=report["message"]
        )

    if not report.get("success", True) and report.get("final_status") == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=report.get("error_message", "Pipeline execution failed.")
        )

    return report


@router.get(
    "/pipeline/history",
    summary="Pipeline Execution Audit Ledger",
    description="Retrieve paginated historical ETL execution records (manual and scheduled)."
)
def list_pipeline_history(
    limit: int = Query(20, ge=1, le=500, description="Max history runs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(None, description="Filter by status: SUCCESS, FAILED, SKIPPED, RUNNING, PARTIAL_SUCCESS"),
    db: Session = Depends(get_db)
):
    """Fetch paginated pipeline execution audit history."""
    total, records = PipelineMonitor.get_history(
        db=db,
        limit=limit,
        offset=offset,
        status_filter=status
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [r.to_dict() for r in records]
    }


@router.get(
    "/pipeline/history/{run_id}",
    summary="Pipeline Execution Details by run_id",
    description="Fetch full operational metrics and parameters for a specific pipeline execution run."
)
def get_pipeline_history_detail(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve full details of a specific pipeline execution."""
    run = PipelineMonitor.get_run_by_id(db, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline execution run '{run_id}' was not found"
        )
    return run.to_dict()


@router.get(
    "/automation/status",
    summary="APScheduler & Ingestion Automation Status",
    description="Retrieve live scheduler operational state, next execution time, and latest pipeline results."
)
def get_automation_status(db: Session = Depends(get_db)):
    """Fetch live scheduler and background automation status."""
    return get_scheduler_status(db=db)
