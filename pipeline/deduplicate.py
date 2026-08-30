"""
Deduplication Engine for Netflix Live Content Analytics Platform.

Performs two-level deduplication:
  Level A: Internal batch deduplication (duplicate show_ids and duplicate title/type/year combinations).
  Level B: Database collision detection against existing stored records.

Provides comprehensive logging and metrics for auditability.
"""

import logging
from typing import List, Dict, Any, Tuple, Set, Optional
from sqlalchemy.orm import Session
import pandas as pd

from database.repository import NetflixRepository
from src.data_cleaning import handle_duplicates

logger = logging.getLogger(__name__)


def deduplicate_records(
    records: List[Dict[str, Any]],
    db_session: Optional[Session] = None,
    mode: str = "insert_new_only"  # 'insert_new_only' or 'upsert'
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Perform two-level deduplication on incoming transformed records.
    
    Args:
        records: List of transformed record dictionaries.
        db_session: Active SQLAlchemy session (if None, only internal deduplication is performed).
        mode: 'insert_new_only' (skips existing DB records) or 'upsert' (includes them for update).
        
    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Any]]:
            - records_to_load: Cleaned records determined ready for database persistence.
            - summary: Detailed accounting of incoming, dropped, new, and existing records.
    """
    logger.info("Starting Deduplication stage...")
    incoming_count = len(records)
    if not records:
        summary = {
            "incoming_records": 0,
            "internal_duplicates": 0,
            "new_records": 0,
            "existing_records": 0,
            "records_ready_to_load": 0,
            "status": "empty"
        }
        return [], summary

    # -------------------------------------------------------------------------
    # Level A: Internal Batch Deduplication
    # -------------------------------------------------------------------------
    # Convert to DataFrame to apply existing subset deduplication logic
    df = pd.DataFrame(records)
    initial_len = len(df)

    # 1. Deduplicate on exact show_id inside incoming batch with conflict awareness
    dup_mask = df.duplicated(subset=["show_id"], keep=False)
    if dup_mask.any():
        conflicting_ids = df[dup_mask]["show_id"].nunique()
        logger.warning(
            f"Deduplication (Level A Conflict): {conflicting_ids} distinct show_id(s) appear multiple times "
            "with potentially conflicting metadata in incoming batch. Deterministic rule applied: "
            "first occurrence retained; subsequent occurrences pruned."
        )

    df = df.drop_duplicates(subset=["show_id"], keep="first")
    id_dups_removed = initial_len - len(df)
    if id_dups_removed > 0:
        logger.info(f"Deduplication (Level A): Removed {id_dups_removed} duplicate show_id entries within batch.")

    # 2. Reuse existing project logic: deduplicate on title + type + release_year
    len_before_subset = len(df)
    df = handle_duplicates(df)
    subset_dups_removed = len_before_subset - len(df)

    internal_duplicates_total = id_dups_removed + subset_dups_removed
    logger.info(
        f"Deduplication (Level A complete): Removed {internal_duplicates_total} internal duplicate(s). "
        f"{len(df):,} unique records retained in batch."
    )

    internally_deduped_records = df.to_dict(orient="records")

    # -------------------------------------------------------------------------
    # Level B: Database Collision Detection
    # -------------------------------------------------------------------------
    new_records: List[Dict[str, Any]] = []
    existing_records: List[Dict[str, Any]] = []

    if db_session is not None:
        repo = NetflixRepository(db_session)
        existing_show_ids: Set[str] = repo.get_existing_show_ids()

        for rec in internally_deduped_records:
            show_id = str(rec.get("show_id"))
            if show_id in existing_show_ids:
                existing_records.append(rec)
            else:
                new_records.append(rec)

        logger.info(
            f"Deduplication (Level B complete): {len(new_records):,} new records, "
            f"{len(existing_records):,} existing records found in database."
        )
    else:
        # No DB session provided (e.g. offline dry run)
        new_records = internally_deduped_records
        existing_records = []
        logger.info("No database session provided; skipping Level B DB collision check.")

    # Determine records ready to load based on ingestion mode
    if mode == "upsert":
        records_to_load = new_records + existing_records
    else:
        # Default: insert new records only, preventing duplicate ingestion
        records_to_load = new_records

    summary = {
        "incoming_records": incoming_count,
        "internal_duplicates": internal_duplicates_total,
        "new_records": len(new_records),
        "existing_records": len(existing_records),
        "records_ready_to_load": len(records_to_load),
        "ingestion_mode": mode,
        "status": "deduplicated"
    }

    logger.info(
        f"Deduplication summary: Incoming={incoming_count}, "
        f"Internal Dups={internal_duplicates_total}, New={len(new_records)}, "
        f"Existing DB={len(existing_records)}, Ready to Load={len(records_to_load)}"
    )

    return records_to_load, summary
