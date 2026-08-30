"""
Catalog Overview Analytics Module for Netflix Live Content Analytics Platform.

Calculates high-level platform KPI counts, ratios, release year spans,
and database freshness directly from the database repository.
"""

from typing import Dict, Any, Optional
import pandas as pd
from database.repository import NetflixRepository


def get_catalog_overview(
    repo: NetflixRepository,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate high-level catalog KPIs from database records.
    
    Args:
        repo: Database repository instance.
        filters: Optional filter dictionary (content_type, min_year, max_year, country, genre, rating, age_group).
        
    Returns:
        Dict[str, Any]: Overview metrics including total titles, movie/tv counts and percentages,
                        year range, average release year, and database freshness.
    """
    f = filters or {}
    df = repo.get_dataframe(
        content_type=f.get("content_type"),
        min_year=f.get("release_year_min") or f.get("min_year"),
        max_year=f.get("release_year_max") or f.get("max_year"),
        country=f.get("country"),
        genre=f.get("genre"),
        rating=f.get("rating"),
        age_group=f.get("age_group")
    )

    total_titles = len(df)
    freshness = repo.get_latest_timestamp()

    if total_titles == 0:
        return {
            "total_titles": 0,
            "movies": 0,
            "tv_shows": 0,
            "movie_percentage": 0.0,
            "tv_show_percentage": 0.0,
            "earliest_release_year": None,
            "latest_release_year": None,
            "average_release_year": None,
            "total_countries": 0,
            "total_genres": 0,
            "database_freshness": freshness
        }

    # Content Type split
    type_counts = df["type"].value_counts().to_dict()
    movies_count = int(type_counts.get("Movie", 0))
    tv_shows_count = int(type_counts.get("TV Show", 0))

    movie_pct = round((movies_count / total_titles) * 100, 2)
    tv_pct = round((tv_shows_count / total_titles) * 100, 2)

    # Release Years
    valid_years = df["release_year"].dropna()
    min_year = int(valid_years.min()) if not valid_years.empty else None
    max_year = int(valid_years.max()) if not valid_years.empty else None
    avg_year = round(float(valid_years.mean()), 1) if not valid_years.empty else None

    # Distinct Countries & Genres
    unique_countries = int(df["primary_country"][df["primary_country"].notnull() & (df["primary_country"] != "Unknown Country")].nunique())
    
    # Calculate unnested unique genres
    genre_series = df["listed_in"].dropna().str.split(",").explode().str.strip()
    unique_genres = int(genre_series.nunique()) if not genre_series.empty else 0

    return {
        "total_titles": total_titles,
        "movies": movies_count,
        "tv_shows": tv_shows_count,
        "movie_percentage": movie_pct,
        "tv_show_percentage": tv_pct,
        "earliest_release_year": min_year,
        "latest_release_year": max_year,
        "average_release_year": avg_year,
        "total_countries": unique_countries,
        "total_genres": unique_genres,
        "database_freshness": freshness
    }
