"""
Duration & Seasonality Analytics Module for Netflix Live Content Analytics Platform.

Analyzes movie runtimes in minutes (statistical distributions, tiers, outliers)
and TV show season longevity (single vs. multi-season renewals).
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


def get_duration_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute movie runtime distributions and TV show season statistics.
    
    Args:
        df: Filtered catalog DataFrame from repository.
        
    Returns:
        Dict[str, Any]: Movie duration stats & tiers, TV show season distributions & longevity.
    """
    total = len(df)
    empty_result = {
        "movies": {
            "count": 0,
            "mean_min": 0.0,
            "median_min": 0.0,
            "min_min": 0.0,
            "max_min": 0.0,
            "duration_tiers": {"labels": [], "values": [], "percentages": []},
            "longest_movies": [],
            "shortest_movies": []
        },
        "tv_shows": {
            "count": 0,
            "mean_seasons": 0.0,
            "median_seasons": 0.0,
            "max_seasons": 0,
            "single_season_pct": 0.0,
            "two_seasons_pct": 0.0,
            "three_plus_seasons_pct": 0.0,
            "season_distribution": {"labels": [], "values": [], "percentages": []},
            "longest_running": []
        }
    }

    if total == 0:
        return empty_result

    # -------------------------------------------------------------------------
    # 1. Movie Duration Analysis
    # -------------------------------------------------------------------------
    movies_df = df[df["type"] == "Movie"]
    if not movies_df.empty and "duration_min" in movies_df.columns:
        durations = movies_df["duration_min"].dropna()
        movie_count = int(durations.count())

        if movie_count > 0:
            mean_min = round(float(durations.mean()), 1)
            median_min = round(float(durations.median()), 1)
            min_min = round(float(durations.min()), 1)
            max_min = round(float(durations.max()), 1)

            # Tiers
            tier_order = ["< 60 min (Short)", "60-90 min (Standard)", "90-120 min (Feature)", "120-150 min (Long)", "> 150 min (Epic)"]
            if "movie_duration_tier" in movies_df.columns:
                tier_counts = movies_df["movie_duration_tier"].value_counts().reindex(tier_order).fillna(0)
                tiers_res = {
                    "labels": list(tier_counts.index),
                    "values": [int(v) for v in tier_counts.values],
                    "percentages": [round((v / movie_count) * 100, 2) for v in tier_counts.values]
                }
            else:
                tiers_res = {"labels": [], "values": [], "percentages": []}

            # Outliers: Longest and Shortest movies
            longest = movies_df.sort_values("duration_min", ascending=False)[
                ["title", "release_year", "primary_country", "duration_min"]
            ].head(5).to_dict(orient="records")

            shortest = movies_df[movies_df["duration_min"] > 0].sort_values("duration_min", ascending=True)[
                ["title", "release_year", "primary_country", "duration_min"]
            ].head(5).to_dict(orient="records")

            movie_res = {
                "count": movie_count,
                "mean_min": mean_min,
                "median_min": median_min,
                "min_min": min_min,
                "max_min": max_min,
                "duration_tiers": tiers_res,
                "longest_movies": longest,
                "shortest_movies": shortest
            }
        else:
            movie_res = empty_result["movies"]
    else:
        movie_res = empty_result["movies"]

    # -------------------------------------------------------------------------
    # 2. TV Show Seasons Analysis
    # -------------------------------------------------------------------------
    tv_df = df[df["type"] == "TV Show"]
    if not tv_df.empty and "seasons" in tv_df.columns:
        seasons = tv_df["seasons"].dropna()
        tv_count = int(seasons.count())

        if tv_count > 0:
            mean_seasons = round(float(seasons.mean()), 1)
            median_seasons = round(float(seasons.median()), 1)
            max_seasons = int(seasons.max())

            single_pct = round(float((seasons == 1).mean() * 100), 2)
            two_pct = round(float((seasons == 2).mean() * 100), 2)
            three_plus_pct = round(float((seasons >= 3).mean() * 100), 2)

            # Seasons 1 to 10 distribution
            season_counts = seasons[seasons <= 10].value_counts().sort_index()
            seasons_res = {
                "labels": [f"{int(s)} Season{'s' if s > 1 else ''}" for s in season_counts.index],
                "values": [int(v) for v in season_counts.values],
                "percentages": [round((v / tv_count) * 100, 2) for v in season_counts.values]
            }

            longest_shows = tv_df.sort_values("seasons", ascending=False)[
                ["title", "release_year", "primary_country", "seasons"]
            ].head(5).to_dict(orient="records")

            tv_res = {
                "count": tv_count,
                "mean_seasons": mean_seasons,
                "median_seasons": median_seasons,
                "max_seasons": max_seasons,
                "single_season_pct": single_pct,
                "two_seasons_pct": two_pct,
                "three_plus_seasons_pct": three_plus_pct,
                "season_distribution": seasons_res,
                "longest_running": longest_shows
            }
        else:
            tv_res = empty_result["tv_shows"]
    else:
        tv_res = empty_result["tv_shows"]

    return {
        "movies": movie_res,
        "tv_shows": tv_res
    }
