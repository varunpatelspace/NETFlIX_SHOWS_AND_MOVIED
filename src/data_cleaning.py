"""
Data Cleaning & Preprocessing Module for Netflix Movies and TV Shows.

This module loads the raw Netflix dataset, handles missing values, removes duplicates,
standardizes date and duration formats, engineer derived features, and outputs a
cleaned dataset ready for exploratory analysis and visualization.
"""

import os
import re
import pandas as pd
import numpy as np


def load_dataset(file_path: str = "data/netflix_titles.csv") -> pd.DataFrame:
    """
    Load raw Netflix dataset from CSV file.
    
    Args:
        file_path (str): Relative or absolute path to raw CSV file.
        
    Returns:
        pd.DataFrame: Raw loaded dataset.
    """
    if not os.path.exists(file_path):
        # Fallback to check relative to script directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt_path = os.path.join(base_dir, file_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            raise FileNotFoundError(f"Dataset not found at '{file_path}' or '{alt_path}'.")
            
    df = pd.read_csv(file_path, encoding="utf-8")
    print(f"[INFO] Successfully loaded dataset with {df.shape[0]:,} rows and {df.shape[1]} columns.")
    return df


def inspect_raw_data(df: pd.DataFrame) -> dict:
    """
    Perform structural and data quality inspection on raw dataset.
    
    Args:
        df (pd.DataFrame): Raw dataset.
        
    Returns:
        dict: Inspection summary containing shape, missing values, duplicates, and column types.
    """
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "missing_counts": df.isnull().sum().to_dict(),
        "missing_percentages": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "exact_duplicates": int(df.duplicated().sum()),
        "subset_duplicates": int(df.duplicated(subset=["title", "type", "release_year"]).sum())
    }
    
    print("\n" + "=" * 60)
    print("DATASET QUALITY INSPECTION SUMMARY")
    print("=" * 60)
    print(f"Total Records: {summary['shape'][0]:,}")
    print(f"Total Columns: {summary['shape'][1]}")
    print("\nMissing Values per Column:")
    for col, count in summary["missing_counts"].items():
        pct = summary["missing_percentages"][col]
        print(f"  - {col:<15}: {count:>5} missing ({pct:>5.2f}%)")
    print(f"\nExact Duplicate Rows: {summary['exact_duplicates']}")
    print(f"Content Duplicates (title + type + release_year): {summary['subset_duplicates']}")
    print("=" * 60 + "\n")
    
    return summary


def clean_text_formatting(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip extra whitespaces and sanitize unicode artifacts in text columns.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with trimmed and sanitized string columns.
    """
    cleaned = df.copy()
    string_cols = cleaned.select_dtypes(include=["object", "string", "str"]).columns
    
    for col in string_cols:
        # Strip leading and trailing whitespace
        cleaned[col] = cleaned[col].astype(str).str.strip()
        # Replace string 'nan' with actual NaN
        cleaned[col] = cleaned[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})
        # Clean replacement character artifacts if present
        cleaned[col] = cleaned[col].apply(lambda x: x.replace("\ufffd", "") if isinstance(x, str) else x)
        
    return cleaned


def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify and remove redundant duplicate titles.
    
    We retain distinct remakes (e.g. Benji 1974 vs Benji 2018) while dropping 
    redundant duplicate ingestion entries sharing title, type, and release_year.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Deduplicated dataframe.
    """
    initial_len = len(df)
    # Remove exact duplicate rows if any
    cleaned = df.drop_duplicates().copy()
    
    # Remove duplicate title + type + release_year keeping the first record
    cleaned = cleaned.drop_duplicates(subset=["title", "type", "release_year"], keep="first").copy()
    removed = initial_len - len(cleaned)
    print(f"[INFO] Deduplication: Removed {removed} duplicate title record(s). Retained {len(cleaned):,} titles.")
    return cleaned


def parse_dates_and_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize 'date_added' to datetime and extract temporal components.
    
    Derives:
        - date_added: pd.Timestamp
        - year_added: Integer year title was ingested
        - month_added: Integer month (1-12)
        - month_name_added: Full month name (e.g., 'January')
        - day_added: Day of month (1-31)
        - release_to_add_lag: Difference in years between release and addition
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with parsed dates and derived temporal features.
    """
    cleaned = df.copy()
    cleaned["date_added"] = pd.to_datetime(cleaned["date_added"], format="mixed", errors="coerce")
    
    # Extract temporal features
    cleaned["year_added"] = cleaned["date_added"].dt.year
    cleaned["month_added"] = cleaned["date_added"].dt.month
    cleaned["month_name_added"] = cleaned["date_added"].dt.month_name()
    cleaned["day_added"] = cleaned["date_added"].dt.day
    
    # For records where date_added is missing, we leave date_added as NaT
    # but impute estimated year_added from release_year for temporal catalog estimation if needed,
    # keeping year_added as Int64 (nullable integer)
    cleaned["year_added"] = cleaned["year_added"].astype("Int64")
    cleaned["month_added"] = cleaned["month_added"].astype("Int64")
    cleaned["day_added"] = cleaned["day_added"].astype("Int64")
    
    # Calculate licensing lag (years between theatrical release and Netflix addition)
    cleaned["release_to_add_lag"] = (cleaned["year_added"] - cleaned["release_year"]).astype("Float64")
    
    return cleaned


def parse_durations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split and normalize 'duration' into numerical minutes for Movies and seasons for TV Shows.
    
    Derives:
        - duration_min: Numerical runtime in minutes for Movies (float/int)
        - seasons: Numerical season count for TV Shows (int)
        - duration_category: Categorical runtime binning for Movies
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with parsed numerical duration columns.
    """
    cleaned = df.copy()
    
    # Extract numerical value from duration string
    cleaned["duration_numeric"] = cleaned["duration"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    
    # Segment by content type
    cleaned["duration_min"] = np.where(
        cleaned["type"] == "Movie",
        cleaned["duration_numeric"],
        np.nan
    )
    
    cleaned["seasons"] = np.where(
        cleaned["type"] == "TV Show",
        cleaned["duration_numeric"],
        np.nan
    )
    
    # Convert seasons to nullable integer
    cleaned["seasons"] = cleaned["seasons"].astype("Int64")
    
    # Bin movie durations into meaningful business tiers
    duration_bins = [0, 60, 90, 120, 150, 500]
    duration_labels = ["< 60 min (Short)", "60-90 min (Standard)", "90-120 min (Feature)", "120-150 min (Long)", "> 150 min (Epic)"]
    cleaned["movie_duration_tier"] = pd.cut(
        cleaned["duration_min"],
        bins=duration_bins,
        labels=duration_labels,
        right=True
    )
    
    # Drop temporary column
    cleaned = cleaned.drop(columns=["duration_numeric"])
    return cleaned


def categorize_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map content ratings into standardized target audience demographics.
    
    Demographic Tiers:
        - 'Adults (18+)': TV-MA, NC-17, R
        - 'Teens (13-17)': TV-14, PG-13
        - 'Older Kids (7-12)': TV-PG, PG
        - 'Little Kids (0-6)': TV-Y, TV-Y7, TV-Y7-FV, TV-G, G
        - 'Unrated': NR, UR, Unavailable
        
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with 'age_group' column.
    """
    cleaned = df.copy()
    
    # Handle missing ratings by imputing 'Unavailable'
    cleaned["rating"] = cleaned["rating"].fillna("Unavailable")
    
    rating_map = {
        "TV-MA": "Adults (18+)",
        "R": "Adults (18+)",
        "NC-17": "Adults (18+)",
        "TV-14": "Teens (13-17)",
        "PG-13": "Teens (13-17)",
        "TV-PG": "Older Kids (7-12)",
        "PG": "Older Kids (7-12)",
        "TV-Y": "Little Kids (0-6)",
        "TV-Y7": "Little Kids (0-6)",
        "TV-Y7-FV": "Little Kids (0-6)",
        "TV-G": "Little Kids (0-6)",
        "G": "Little Kids (0-6)",
        "NR": "Unrated",
        "UR": "Unrated",
        "Unavailable": "Unrated"
    }
    
    cleaned["age_group"] = cleaned["rating"].map(rating_map).fillna("Unrated")
    return cleaned


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strategically handle missing values without data loss.
    
    Justifications:
        - director: Filled with 'Unknown Director' (32.5% missing, especially common in TV series).
        - cast: Filled with 'Unknown Cast' (documentaries, animations, or unlisted ensembles).
        - country: Filled with 'Unknown Country' (multi-national licensing gaps).
        - rating: Imputed as 'Unavailable' (10 missing records).
        - date_added: Retained as NaT in timestamp; marked in an ingestion flag.
        
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with strategic imputations.
    """
    cleaned = df.copy()
    
    cleaned["director"] = cleaned["director"].fillna("Unknown Director")
    cleaned["cast"] = cleaned["cast"].fillna("Unknown Cast")
    cleaned["country"] = cleaned["country"].fillna("Unknown Country")
    cleaned["rating"] = cleaned["rating"].fillna("Unavailable")
    
    # Create helper flags for missingness awareness
    cleaned["has_director_info"] = cleaned["director"] != "Unknown Director"
    cleaned["has_cast_info"] = cleaned["cast"] != "Unknown Cast"
    cleaned["has_country_info"] = cleaned["country"] != "Unknown Country"
    cleaned["has_date_added"] = cleaned["date_added"].notnull()
    
    return cleaned


def engineer_multi_value_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive primary attributes and multi-value indicators from comma-separated fields.
    
    Features:
        - primary_country: First producing country listed
        - is_multi_country: Boolean flag for international co-productions
        - country_count: Number of participating countries
        - primary_genre: First genre listed in categories
        - genre_count: Total genres associated with the title
        - cast_count: Total actors listed in cast
        
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with engineered multi-value features.
    """
    cleaned = df.copy()
    
    # Country parsing
    cleaned["primary_country"] = cleaned["country"].apply(
        lambda x: x.split(",")[0].strip() if pd.notnull(x) else "Unknown Country"
    )
    cleaned["country_count"] = cleaned["country"].apply(
        lambda x: len([c.strip() for c in x.split(",")]) if pd.notnull(x) and x != "Unknown Country" else 0
    )
    cleaned["is_multi_country"] = cleaned["country_count"] > 1
    
    # Genre parsing
    cleaned["primary_genre"] = cleaned["listed_in"].apply(
        lambda x: x.split(",")[0].strip() if pd.notnull(x) else "Unknown Genre"
    )
    cleaned["genre_count"] = cleaned["listed_in"].apply(
        lambda x: len([g.strip() for g in x.split(",")]) if pd.notnull(x) else 0
    )
    
    # Cast counting
    cleaned["cast_count"] = cleaned["cast"].apply(
        lambda x: len([c.strip() for c in x.split(",")]) if pd.notnull(x) and x != "Unknown Cast" else 0
    )
    
    return cleaned


def clean_netflix_pipeline(raw_path: str = "data/netflix_titles.csv", 
                           output_path: str = "data/netflix_cleaned.csv") -> pd.DataFrame:
    """
    Execute the end-to-end data cleaning pipeline and persist cleaned data.
    
    Args:
        raw_path (str): Path to raw CSV.
        output_path (str): Path to save cleaned CSV.
        
    Returns:
        pd.DataFrame: Fully cleaned and engineered dataframe.
    """
    print("=" * 60)
    print("STARTING NETFLIX DATA CLEANING PIPELINE")
    print("=" * 60)
    
    # 1. Load Raw Dataset
    raw_df = load_dataset(raw_path)
    
    # 2. Inspect Raw Data
    inspect_raw_data(raw_df)
    
    # 3. Clean Text Formatting & Whitespace
    step1 = clean_text_formatting(raw_df)
    
    # 4. Remove Duplicates
    step2 = handle_duplicates(step1)
    
    # 5. Parse Dates and Temporal Components
    step3 = parse_dates_and_times(step2)
    
    # 6. Parse Durations
    step4 = parse_durations(step3)
    
    # 7. Categorize Ratings & Age Groups
    step5 = categorize_ratings(step4)
    
    # 8. Handle Missing Values
    step6 = handle_missing_values(step5)
    
    # 9. Engineer Multi-Value Features
    cleaned_df = engineer_multi_value_features(step6)
    
    # Save cleaned dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cleaned_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n[SUCCESS] Cleaned dataset saved to '{output_path}'.")
    print(f"Final shape: {cleaned_df.shape[0]:,} rows and {cleaned_df.shape[1]} columns.\n")
    print("=" * 60)
    
    return cleaned_df


# Helper unnesting utility functions for EDA
def get_exploded_series(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Extract and unnest comma-separated values into individual occurrences.
    
    Args:
        df (pd.DataFrame): Dataframe.
        column (str): Column name containing comma-separated strings.
        
    Returns:
        pd.Series: Exploded series with single items per row.
    """
    series = df[column].dropna().astype(str)
    series = series[~series.isin(["Unknown Country", "Unknown Director", "Unknown Cast"])]
    return series.str.split(",").explode().str.strip()


def get_movies_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataset for Movies only."""
    return df[df["type"] == "Movie"].copy()


def get_tvshows_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataset for TV Shows only."""
    return df[df["type"] == "TV Show"].copy()


if __name__ == "__main__":
    # Test and execute pipeline directly
    cleaned_data = clean_netflix_pipeline()
    print("Sample records from cleaned dataset:")
    print(cleaned_data[["title", "type", "release_year", "year_added", "duration_min", "seasons", "age_group", "primary_country"]].head())
