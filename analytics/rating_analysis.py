"""
Rating & Demographics Analytics Module for Netflix Live Content Analytics Platform.

Analyzes content maturity certifications and target audience demographic tiers.
"""

from typing import Dict, Any
import pandas as pd


def get_rating_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute rating distributions, age group demographics, and type cross-tabulations.
    
    Args:
        df: Filtered catalog DataFrame from repository.
        
    Returns:
        Dict[str, Any]: Rating distributions, demographic age group shares,
                        and Movie vs TV Show cross-tabulation.
    """
    total = len(df)
    if total == 0:
        return {
            "ratings": {"labels": [], "values": [], "percentages": []},
            "age_groups": {"labels": [], "values": [], "percentages": []},
            "type_by_rating": {"ratings": [], "movies": [], "tv_shows": []},
            "dominant_rating": None,
            "dominant_age_group": None
        }

    # 1. Rating Distribution (Sorted by frequency)
    rating_counts = df["rating"].fillna("Unavailable").value_counts()
    ratings_res = {
        "labels": list(rating_counts.index),
        "values": [int(v) for v in rating_counts.values],
        "percentages": [round((v / total) * 100, 2) for v in rating_counts.values]
    }

    # 2. Demographic Age Group Distribution
    age_counts = df["age_group"].fillna("Unrated").value_counts()
    age_groups_res = {
        "labels": list(age_counts.index),
        "values": [int(v) for v in age_counts.values],
        "percentages": [round((v / total) * 100, 2) for v in age_counts.values]
    }

    # 3. Cross-Tabulation: Content Type by Top 10 Ratings
    top10_ratings = list(rating_counts.head(10).index)
    subset = df[df["rating"].isin(top10_ratings)]
    if not subset.empty:
        ct = pd.crosstab(subset["rating"], subset["type"]).reindex(top10_ratings).fillna(0)
        type_by_rating_res = {
            "ratings": top10_ratings,
            "movies": [int(ct.loc[r, "Movie"]) if "Movie" in ct.columns else 0 for r in top10_ratings],
            "tv_shows": [int(ct.loc[r, "TV Show"]) if "TV Show" in ct.columns else 0 for r in top10_ratings]
        }
    else:
        type_by_rating_res = {"ratings": [], "movies": [], "tv_shows": []}

    dominant_rating = ratings_res["labels"][0] if ratings_res["labels"] else None
    dominant_age_group = age_groups_res["labels"][0] if age_groups_res["labels"] else None

    return {
        "ratings": ratings_res,
        "age_groups": age_groups_res,
        "type_by_rating": type_by_rating_res,
        "dominant_rating": dominant_rating,
        "dominant_age_group": dominant_age_group
    }
