"""
Master Pipeline Runner for Netflix Live Content Analytics Platform.

Orchestrates the complete end-to-end ETL workflow:
  1. Extract raw data from configured source (pipeline.fetch_data)
  2. Validate incoming schema and records (pipeline.validate_data)
  3. Clean text and impute missing values (pipeline.clean_data)
  4. Transform records for database persistence (pipeline.transform_data)
  5. Deduplicate against batch and active database (pipeline.deduplicate)
  6. Load records transactionally to database (pipeline.load_data)
  7. Generate comprehensive audit report with stage metrics and execution status.
"""

import sys
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from config.settings import DATA_UPDATE_MODE
from database.database import SessionLocal, init_db
from database.repository import NetflixRepository
from pipeline.fetch_data import extract_raw_data
from pipeline.validate_data import validate_raw_data, DataValidationError
from pipeline.clean_data import clean_dataset
from pipeline.transform_data import transform_for_database
from pipeline.deduplicate import deduplicate_records
from pipeline.load_data import load_records

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("PipelineRunner")


def run_pipeline(
    source_type: Optional[str] = None,
    source_path: Optional[str] = None,
    mode: Optional[str] = None,
    db_session: Optional[Session] = None,
    strict_schema: bool = False,
    **source_kwargs
) -> Dict[str, Any]:
    """
    Execute the automated end-to-end ETL pipeline.
    
    Args:
        source_type: Data source type ('csv' or 'api').
        source_path: Path to dataset or API URL.
        mode: Ingestion mode ('insert_new_only' or 'upsert'). Defaults to DATA_UPDATE_MODE.
        db_session: Optional external SQLAlchemy session.
        strict_schema: Whether to require all 12 standard columns.
        **source_kwargs: Extra parameters for the data source.
        
    Returns:
        Dict[str, Any]: Comprehensive pipeline execution report.
    """
    effective_mode = (mode or DATA_UPDATE_MODE).lower()
    pipeline_id = f"pipe_{uuid.uuid4().hex[:8]}"
    start_time = datetime.now(timezone.utc)
    
    print("\n" + "=" * 70)
    print(f"  NETFLIX LIVE PIPELINE EXECUTION — [{pipeline_id}]")
    print("=" * 70)
    logger.info(f"Starting ETL Pipeline [{pipeline_id}] (mode='{mode}')...")

    # Pipeline audit report structure
    report: Dict[str, Any] = {
        "pipeline_id": pipeline_id,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "duration_seconds": None,
        "source_metadata": None,
        "validation_summary": None,
        "cleaning_summary": None,
        "transformation_summary": None,
        "deduplication_summary": None,
        "load_summary": None,
        "incremental_metrics": {
            "incoming_records": 0,
            "internal_duplicates": 0,
            "existing_records": 0,
            "new_records": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "mode": effective_mode
        },
        "final_database_total": 0,
        "final_status": "FAILED",
        "error_message": None
    }

    # Manage local session if not provided
    owns_session = db_session is None
    session = db_session or SessionLocal()

    try:
        # Initialize database tables
        init_db()

        # ---------------------------------------------------------------------
        # 1. EXTRACT
        # ---------------------------------------------------------------------
        print("\n>>> [1/6] EXTRACT: Fetching raw catalog records...")
        raw_df, extract_meta = extract_raw_data(
            source_type=source_type,
            source_path=source_path,
            **source_kwargs
        )
        report["source_metadata"] = extract_meta
        print(f"    Fetched {len(raw_df):,} raw records from {extract_meta['source_name']}.")

        # ---------------------------------------------------------------------
        # 2. VALIDATE
        # ---------------------------------------------------------------------
        print("\n>>> [2/6] VALIDATE: Enforcing schema and row-level quality...")
        valid_df, invalid_df, val_summary = validate_raw_data(raw_df, strict_schema=strict_schema)
        report["validation_summary"] = val_summary
        print(f"    Valid records: {val_summary['valid_records']:,} | Invalid records: {val_summary['invalid_records']:,}")
        if val_summary['invalid_records'] > 0:
            print(f"    Quarantined reasons: {val_summary['invalid_reasons']}")

        if valid_df.empty:
            raise DataValidationError("No valid records remaining after validation.")

        # ---------------------------------------------------------------------
        # 3. CLEAN
        # ---------------------------------------------------------------------
        print("\n>>> [3/6] CLEAN: Executing whitespace, text, and missingness imputation...")
        cleaned_df, clean_summary = clean_dataset(valid_df)
        report["cleaning_summary"] = clean_summary
        print(f"    Cleaned records: {clean_summary['output_records']:,} with {clean_summary['derived_columns_count']} features.")

        # ---------------------------------------------------------------------
        # 4. TRANSFORM
        # ---------------------------------------------------------------------
        print("\n>>> [4/6] TRANSFORM: Standardizing types and preparing database payloads...")
        _, transformed_records, trans_summary = transform_for_database(cleaned_df)
        report["transformation_summary"] = trans_summary
        print(f"    Transformed {trans_summary['transformed_records']:,} payloads ready for database.")

        # ---------------------------------------------------------------------
        # 5. DEDUPLICATE
        # ---------------------------------------------------------------------
        print(f"\n>>> [5/6] DEDUPLICATE: Detecting internal duplicates and DB collisions (mode='{effective_mode}')...")
        records_to_load, dedup_summary = deduplicate_records(
            records=transformed_records,
            db_session=session,
            mode=effective_mode
        )
        report["deduplication_summary"] = dedup_summary
        print(
            f"    Incoming: {dedup_summary['incoming_records']:,} | "
            f"Internal Dups: {dedup_summary['internal_duplicates']:,} | "
            f"New: {dedup_summary['new_records']:,} | "
            f"Existing in DB: {dedup_summary['existing_records']:,}"
        )

        # ---------------------------------------------------------------------
        # 6. LOAD
        # ---------------------------------------------------------------------
        print(f"\n>>> [6/6] LOAD: Persisting records to database (mode='{effective_mode}')...")
        total_loaded, load_summary = load_records(
            records=records_to_load,
            db_session=session,
            mode=effective_mode
        )
        report["load_summary"] = load_summary
        print(f"    Inserted: {load_summary['inserted']:,} | Updated: {load_summary['updated']:,} | Skipped: {load_summary['skipped']:,}")

        # Final database total count
        repo = NetflixRepository(session)
        final_total = repo.get_total_count()
        report["final_database_total"] = final_total

        # Consolidated Incremental Metrics Breakdown
        report["incremental_metrics"] = {
            "incoming_records": dedup_summary.get("incoming_records", 0),
            "internal_duplicates": dedup_summary.get("internal_duplicates", 0),
            "existing_records": dedup_summary.get("existing_records", 0),
            "new_records": dedup_summary.get("new_records", 0),
            "inserted": load_summary.get("inserted", 0),
            "updated": load_summary.get("updated", 0),
            "skipped": load_summary.get("skipped", 0),
            "failed": load_summary.get("failed", 0),
            "mode": effective_mode
        }

        # Set final execution status
        if val_summary["invalid_records"] > 0:
            report["final_status"] = "PARTIAL_SUCCESS"
        else:
            report["final_status"] = "SUCCESS"

    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}", exc_info=True)
        report["final_status"] = "FAILED"
        report["error_message"] = str(e)
        print(f"\n[ERROR] Pipeline failed with error: {e}")

    finally:
        end_time = datetime.now(timezone.utc)
        report["end_time"] = end_time.isoformat()
        report["duration_seconds"] = round((end_time - start_time).total_seconds(), 4)

        if owns_session:
            session.close()

    print("\n" + "=" * 70)
    print(f"  PIPELINE EXECUTION {report['final_status']} IN {report['duration_seconds']}s")
    print(f"  Final Database Record Count: {report['final_database_total']:,}")
    print("=" * 70 + "\n")

    return report


if __name__ == "__main__":
    # Direct execution demonstration
    summary = run_pipeline()
    print("Summary Output:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
