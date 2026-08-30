"""
Data Validation Module for Netflix Live Content Analytics Platform.

Performs schema enforcement, type checking, and row-level data quality validation
on incoming raw datasets. Distinguishes fatal dataset-level errors from row-level anomalies.
"""

import logging
from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Mandatory columns that must exist in the dataset schema
CRITICAL_SCHEMA_COLUMNS = ["show_id", "type", "title"]

# Standard baseline schema columns expected from the Netflix catalog
STANDARD_CATALOG_COLUMNS = [
    "show_id", "title", "director", "cast", "country", 
    "date_added", "release_year", "rating", "duration", 
    "listed_in", "description", "type"
]

# Valid primary content types
VALID_CONTENT_TYPES = {"Movie", "TV Show"}


class DataValidationError(Exception):
    """Raised when a fatal dataset-level validation failure occurs."""
    pass


def validate_raw_data(
    df: pd.DataFrame,
    strict_schema: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Validate incoming raw dataset against schema and row-level quality rules.
    
    Args:
        df: Raw DataFrame extracted from data source.
        strict_schema: If True, requires all 12 standard columns. If False, requires CRITICAL_SCHEMA_COLUMNS.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
            - valid_df: DataFrame containing all valid, ingestible rows.
            - invalid_df: DataFrame containing quarantined rows with an added 'validation_error' column.
            - summary: Structured validation metrics dictionary.
            
    Raises:
        DataValidationError: On fatal dataset-level errors (empty DataFrame or missing critical columns).
    """
    logger.info("Starting Data Validation stage...")

    # -------------------------------------------------------------------------
    # A. Fatal Dataset-Level Checks
    # -------------------------------------------------------------------------
    if df is None:
        raise DataValidationError("Fatal Validation Error: Provided dataset is None.")

    if not isinstance(df, pd.DataFrame):
        raise DataValidationError(f"Fatal Validation Error: Expected pd.DataFrame, got {type(df)}.")

    total_records = len(df)
    if total_records == 0:
        raise DataValidationError("Fatal Validation Error: Dataset is completely empty (0 records).")

    # Check required columns
    required_cols = STANDARD_CATALOG_COLUMNS if strict_schema else CRITICAL_SCHEMA_COLUMNS
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise DataValidationError(
            f"Fatal Validation Error: Missing mandatory columns from schema: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    warnings: List[str] = []
    # Check for non-critical standard columns missing
    optional_missing = [col for col in STANDARD_CATALOG_COLUMNS if col not in df.columns]
    if optional_missing:
        warnings.append(f"Non-critical standard catalog columns missing: {optional_missing}")
        logger.warning(warnings[-1])

    # -------------------------------------------------------------------------
    # B. Row-Level Validation
    # -------------------------------------------------------------------------
    working_df = df.copy()
    invalid_reasons: Dict[str, int] = {
        "missing_show_id": 0,
        "missing_title": 0,
        "invalid_type": 0,
        "invalid_release_year": 0,
    }

    # Initialize mask for invalid rows
    is_invalid = pd.Series(False, index=working_df.index)
    error_descriptions = pd.Series("", index=working_df.index, dtype=str)

    # 1. Missing or blank show_id
    show_id_series = working_df["show_id"].astype(str).str.strip()
    bad_id = working_df["show_id"].isnull() | (show_id_series.isin(["", "nan", "None"]))
    if bad_id.any():
        count = int(bad_id.sum())
        invalid_reasons["missing_show_id"] = count
        is_invalid |= bad_id
        error_descriptions[bad_id] += "Missing or empty show_id; "

    # 2. Missing or blank title
    title_series = working_df["title"].astype(str).str.strip()
    bad_title = working_df["title"].isnull() | (title_series.isin(["", "nan", "None"]))
    if bad_title.any():
        count = int(bad_title.sum())
        invalid_reasons["missing_title"] = count
        is_invalid |= bad_title
        error_descriptions[bad_title] += "Missing or empty title; "

    # 3. Invalid content type
    if "type" in working_df.columns:
        type_series = working_df["type"].astype(str).str.strip()
        bad_type = ~type_series.isin(VALID_CONTENT_TYPES)
        if bad_type.any():
            count = int(bad_type.sum())
            invalid_reasons["invalid_type"] = count
            is_invalid |= bad_type
            error_descriptions[bad_type] += "Invalid content type (must be 'Movie' or 'TV Show'); "

    # 4. Invalid release_year (if present)
    if "release_year" in working_df.columns:
        # Check numeric convertibility and reasonable year range (1900 to 2050)
        numeric_year = pd.to_numeric(working_df["release_year"], errors="coerce")
        bad_year = working_df["release_year"].notnull() & (
            numeric_year.isnull() | (numeric_year < 1900) | (numeric_year > 2050)
        )
        if bad_year.any():
            count = int(bad_year.sum())
            invalid_reasons["invalid_release_year"] = count
            is_invalid |= bad_year
            error_descriptions[bad_year] += "Invalid release_year; "

    # Split dataset
    valid_df = working_df[~is_invalid].copy()
    invalid_df = working_df[is_invalid].copy()
    if not invalid_df.empty:
        invalid_df["validation_error"] = error_descriptions[is_invalid].str.rstrip("; ")

    summary = {
        "total_records": total_records,
        "valid_records": len(valid_df),
        "invalid_records": len(invalid_df),
        "missing_required_columns": missing_cols,
        "invalid_reasons": {k: v for k, v in invalid_reasons.items() if v > 0},
        "warnings": warnings,
        "is_valid": len(invalid_df) == 0
    }

    logger.info(
        f"Validation complete: {len(valid_df):,} valid records, "
        f"{len(invalid_df):,} invalid records out of {total_records:,} total."
    )
    if len(invalid_df) > 0:
        logger.warning(f"Row validation issues detected: {summary['invalid_reasons']}")

    return valid_df, invalid_df, summary
