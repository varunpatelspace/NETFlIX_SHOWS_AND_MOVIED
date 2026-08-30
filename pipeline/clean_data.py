"""
Data Cleaning Module for Netflix Live Content Analytics Platform.

Reuses the battle-tested cleaning and imputation logic from `src.data_cleaning`
without code duplication, providing a clean adapter for the live ETL pipeline.
"""

import logging
from typing import Tuple, Dict, Any
import pandas as pd

# Directly reuse functions from existing project
from src.data_cleaning import (
    clean_text_formatting,
    parse_dates_and_times,
    parse_durations,
    categorize_ratings,
    handle_missing_values,
    engineer_multi_value_features
)

logger = logging.getLogger(__name__)


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Execute data cleaning and feature derivation on validated raw data.
    
    Reuses existing project algorithms:
      1. clean_text_formatting: Strips whitespaces and cleans unicode artifacts.
      2. parse_dates_and_times: Parses ISO dates, derives year/month/day and lag.
      3. parse_durations: Extracts duration_min, seasons, and runtime tiers.
      4. categorize_ratings: Maps 14 ratings into 5 demographic age groups.
      5. handle_missing_values: Strategic imputation for director, cast, country, rating.
      6. engineer_multi_value_features: Derives primary_country, country_count, primary_genre, etc.
      
    Args:
        df: Validated raw DataFrame.
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]:
            - cleaned_df: Cleaned and feature-engineered DataFrame.
            - cleaning_summary: Operational metrics regarding missing value imputations.
    """
    logger.info("Starting Data Cleaning & Feature Engineering stage...")
    initial_count = len(df)

    # 1. Clean Text Formatting & Whitespace
    step1 = clean_text_formatting(df)

    # 1b. Ensure expected catalog columns exist with None defaults for minimal schema batches
    standard_optional_cols = [
        "director", "cast", "country", "date_added", "release_year", 
        "rating", "duration", "listed_in", "description"
    ]
    for col in standard_optional_cols:
        if col not in step1.columns:
            step1[col] = None

    # 2. Parse Dates and Temporal Components
    step2 = parse_dates_and_times(step1)

    # 3. Parse Durations
    step3 = parse_durations(step2)

    # 4. Categorize Ratings & Age Groups
    step4 = categorize_ratings(step3)

    # 5. Handle Missing Values (Strategic Imputation)
    step5 = handle_missing_values(step4)

    # 6. Engineer Multi-Value Features
    cleaned_df = engineer_multi_value_features(step5)

    cleaning_summary = {
        "input_records": initial_count,
        "output_records": len(cleaned_df),
        "derived_columns_count": len(cleaned_df.columns),
        "imputed_directors": int((cleaned_df["director"] == "Unknown Director").sum()),
        "imputed_cast": int((cleaned_df["cast"] == "Unknown Cast").sum()),
        "imputed_country": int((cleaned_df["country"] == "Unknown Country").sum()),
        "imputed_rating": int((cleaned_df["rating"] == "Unavailable").sum()),
        "status": "cleaned"
    }

    logger.info(
        f"Data Cleaning complete: {len(cleaned_df):,} records processed with "
        f"{len(cleaned_df.columns)} total feature columns."
    )

    return cleaned_df, cleaning_summary
