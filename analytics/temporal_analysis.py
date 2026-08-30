"""
Temporal & Trend Analytics Module for Netflix Live Content Analytics Platform.

Analyzes content additions over years, premiere release timelines,
monthly ingestion seasonality, and content licensing latency.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


def get_temporal_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute time series, growth trajectories, and seasonality from catalog DataFrame.
    
    Args:
        df: Filtered catalog DataFrame from repository.
        
    Returns:
        Dict[str, Any]: Yearly additions, release trends, monthly seasonality,
                        licensing lag statistics, and comparative Movie vs TV additions.
    """
    total = len(df)
    if total == 0:
        return {
            "yearly_additions": {"years": [], "counts": [], "growth_rate_pct": []},
            "yearly_releases": {"years": [], "counts": []},
            "monthly_seasonality": {"months": [], "counts": [], "percentages": []},
            "licensing_lag_stats": {
                "mean_lag_years": 0.0,
                "median_lag_years": 0.0,
                "same_year_release_pct": 0.0,
                "within_2_years_pct": 0.0
            },
            "comparative_yearly": {"years": [], "movies": [], "tv_shows": []}
        }

    # 1. Additions by Year (year_added >= 2008)
    valid_added = df["year_added"].dropna().astype(int)
    yearly_counts = valid_added.value_counts().sort_index()
    if not yearly_counts.empty:
        # Calculate percentage growth rate
        pct_change = yearly_counts.pct_change().fillna(0) * 100
        yearly_additions = {
            "years": [int(y) for y in yearly_counts.index],
            "counts": [int(v) for v in yearly_counts.values],
            "growth_rate_pct": [round(float(p), 2) for p in pct_change.values]
        }
    else:
        yearly_additions = {"years": [], "counts": [], "growth_rate_pct": []}

    # 2. Content by Release Year (focus on modern cinematic era: 1995 to present)
    valid_releases = df["release_year"].dropna().astype(int)
    modern_releases = valid_releases[valid_releases >= 1995].value_counts().sort_index()
    yearly_releases = {
        "years": [int(y) for y in modern_releases.index],
        "counts": [int(v) for v in modern_releases.values]
    }

    # 3. Monthly Addition Seasonality (Standardized Jan-Dec order)
    months_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    if "month_name_added" in df.columns:
        month_counts = df["month_name_added"].dropna().value_counts().reindex(months_order).fillna(0)
        total_monthly = month_counts.sum() or 1
        monthly_seasonality = {
            "months": list(month_counts.index),
            "counts": [int(v) for v in month_counts.values],
            "percentages": [round((v / total_monthly) * 100, 2) for v in month_counts.values]
        }
    else:
        monthly_seasonality = {"months": months_order, "counts": [0]*12, "percentages": [0.0]*12}

    # 4. Licensing Lag Statistics (Release Year to Netflix Addition Year)
    if "release_to_add_lag" in df.columns:
        valid_lag = df["release_to_add_lag"].dropna()
        if not valid_lag.empty:
            lag_stats = {
                "mean_lag_years": round(float(valid_lag.mean()), 2),
                "median_lag_years": round(float(valid_lag.median()), 2),
                "same_year_release_pct": round(float((valid_lag <= 0).mean() * 100), 2),
                "within_2_years_pct": round(float((valid_lag <= 2).mean() * 100), 2)
            }
        else:
            lag_stats = {"mean_lag_years": 0.0, "median_lag_years": 0.0, "same_year_release_pct": 0.0, "within_2_years_pct": 0.0}
    else:
        lag_stats = {"mean_lag_years": 0.0, "median_lag_years": 0.0, "same_year_release_pct": 0.0, "within_2_years_pct": 0.0}

    # 5. Comparative Movie vs TV Show Additions over time
    if "year_added" in df.columns and "type" in df.columns:
        valid_added_df = df[df["year_added"].notnull() & (df["year_added"] >= 2012)]
        if not valid_added_df.empty:
            ct = pd.crosstab(valid_added_df["year_added"].astype(int), valid_added_df["type"])
            years = [int(y) for y in ct.index]
            movies = [int(ct.loc[y, "Movie"]) if "Movie" in ct.columns else 0 for y in ct.index]
            tv_shows = [int(ct.loc[y, "TV Show"]) if "TV Show" in ct.columns else 0 for y in ct.index]
            comparative_yearly = {
                "years": years,
                "movies": movies,
                "tv_shows": tv_shows
            }
        else:
            comparative_yearly = {"years": [], "movies": [], "tv_shows": []}
    else:
        comparative_yearly = {"years": [], "movies": [], "tv_shows": []}

    return {
        "yearly_additions": yearly_additions,
        "yearly_releases": yearly_releases,
        "monthly_seasonality": monthly_seasonality,
        "licensing_lag_stats": lag_stats,
        "comparative_yearly": comparative_yearly
    }
