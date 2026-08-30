"""
Data Transformation Module for Netflix Live Content Analytics Platform.

Prepares cleaned DataFrames for database persistence:
  - Normalizes nulls/NaNs into clean Python None values.
  - Formats date_added into datetime.date objects or None.
  - Enforces database column types and ensures all schema fields are present.
  - Converts records into optimized dictionary payloads for bulk database insertion.
"""

import logging
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Expected columns for netflix_content table
DATABASE_COLUMNS = [
    "show_id", "type", "title", "director", "cast", "country", 
    "date_added", "release_year", "rating", "duration", "listed_in", 
    "description", "year_added", "month_added", "month_name_added", 
    "day_added", "release_to_add_lag", "duration_min", "seasons", 
    "movie_duration_tier", "age_group", "has_director_info", 
    "has_cast_info", "has_country_info", "has_date_added", 
    "primary_country", "country_count", "is_multi_country", 
    "primary_genre", "genre_count", "cast_count"
]


def transform_for_database(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Transform cleaned DataFrame into database-compatible format and dictionaries.
    
    Args:
        df: Cleaned and feature-engineered DataFrame.
        
    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
            - transformed_df: DataFrame with standardized schema.
            - records: List of dictionary payloads ready for bulk database insertion.
            - summary: Operational transformation metrics.
    """
    logger.info("Starting Data Transformation stage...")
    transformed = df.copy()

    # 1. Ensure all expected database columns exist with sensible defaults
    for col in DATABASE_COLUMNS:
        if col not in transformed.columns:
            transformed[col] = None

    # 2. Format date_added to date objects
    if "date_added" in transformed.columns:
        def _to_date(val):
            if pd.isnull(val):
                return None
            try:
                ts = pd.to_datetime(val)
                return ts.date() if pd.notnull(ts) else None
            except Exception:
                return None
        transformed["date_added"] = transformed["date_added"].apply(_to_date)

    # 3. Cast numeric columns safely (handling nullable integers and floats)
    int_cols = ["release_year", "year_added", "month_added", "day_added", "seasons", "country_count", "genre_count", "cast_count"]
    for col in int_cols:
        if col in transformed.columns:
            transformed[col] = pd.to_numeric(transformed[col], errors="coerce").astype("Int64")

    float_cols = ["duration_min", "release_to_add_lag"]
    for col in float_cols:
        if col in transformed.columns:
            transformed[col] = pd.to_numeric(transformed[col], errors="coerce").astype("Float64")

    # 4. Cast boolean flags
    bool_cols = ["has_director_info", "has_cast_info", "has_country_info", "has_date_added", "is_multi_country"]
    for col in bool_cols:
        if col in transformed.columns:
            transformed[col] = transformed[col].fillna(False).astype(bool)

    # 5. Filter only database-mapped columns
    transformed = transformed[DATABASE_COLUMNS].copy()

    # 6. Convert to list of dicts with NaN normalized to None
    records: List[Dict[str, Any]] = []
    for r in transformed.to_dict(orient="records"):
        clean_rec = {}
        for k, v in r.items():
            # Check for pandas/numpy nulls
            if pd.isna(v):
                clean_rec[k] = None
            elif isinstance(v, np.generic):
                clean_rec[k] = v.item()
            else:
                clean_rec[k] = v
        records.append(clean_rec)

    summary = {
        "transformed_records": len(records),
        "columns_aligned": len(DATABASE_COLUMNS),
        "status": "transformed"
    }

    logger.info(
        f"Data Transformation complete: {len(records):,} records prepared "
        f"for database loading across {len(DATABASE_COLUMNS)} columns."
    )

    return transformed, records, summary
