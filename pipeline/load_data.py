"""
Database Loading Module for Netflix Live Content Analytics Platform.

Persists validated, cleaned, and deduplicated records to the database
using batch operations and repository patterns. Guarantees transactional
integrity and provides detailed load statistics.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from database.database import init_db, SessionLocal, get_db_context
from database.repository import NetflixRepository

logger = logging.getLogger(__name__)


def load_records(
    records: List[Dict[str, Any]],
    db_session: Optional[Session] = None,
    mode: str = "insert_new_only",
    batch_size: int = 1000
) -> Tuple[int, Dict[str, Any]]:
    """
    Load processed records into the database.
    
    Args:
        records: List of cleaned, deduplicated record dictionaries.
        db_session: Optional external SQLAlchemy session. If None, manages own session.
        mode: 'insert_new_only' or 'upsert'.
        batch_size: Chunk size for chunked bulk inserts.
        
    Returns:
        Tuple[int, Dict[str, Any]]:
            - total_loaded: Total number of rows inserted/updated.
            - summary: Dictionary with {"inserted", "updated", "skipped", "failed", "status"}.
    """
    logger.info(f"Starting Database Load stage ({len(records):,} records, mode='{mode}')...")

    # Initialize tables if not yet created
    init_db()

    summary = {
        "records_received": len(records),
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "status": "pending"
    }

    if not records:
        summary["status"] = "noop_empty"
        logger.info("Database Load: No records provided to load.")
        return 0, summary

    # Session management helper
    def _execute_load(session: Session) -> Tuple[int, Dict[str, Any]]:
        repo = NetflixRepository(session)
        inserted_count = 0
        updated_count = 0

        # Chunk records to avoid excessive memory or SQLite parameter limits
        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            if mode == "upsert":
                res = repo.upsert_batch(chunk)
                inserted_count += res["inserted"]
                updated_count += res["updated"]
            else:
                inserted_count += repo.insert_batch(chunk)

        summary["inserted"] = inserted_count
        summary["updated"] = updated_count
        summary["skipped"] = len(records) - (inserted_count + updated_count)
        summary["status"] = "loaded"

        total = inserted_count + updated_count
        logger.info(
            f"Database Load complete: {inserted_count:,} inserted, "
            f"{updated_count:,} updated, {summary['skipped']} skipped."
        )
        return total, summary

    if db_session is not None:
        # Use caller-provided session (caller manages overall transaction)
        return _execute_load(db_session)
    else:
        # Own transaction management
        with get_db_context() as session:
            return _execute_load(session)
