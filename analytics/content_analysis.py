"""
Content Type & Genre Analytics Module for Netflix Live Content Analytics Platform.

Analyzes catalog composition across Movies, TV Shows, and content categories.
"""

from typing import Dict, Any
import pandas as pd
from src.data_cleaning import get_exploded_series


def get_content_analysis(df: pd.DataFrame, top_n: int = 15) -> Dict[str, Any]:
    """
    Analyze content types and genre concentrations from a filtered DataFrame.
    
    Args:
        df: Filtered catalog DataFrame from repository.
        top_n: Number of top genres to return.
        
    Returns:
        Dict[str, Any]: Content type split, top genres overall, movie genres,
                        TV genres, and multi-genre proportions.
    """
    total = len(df)
    if total == 0:
        return {
            "content_type": {"labels": [], "values": [], "percentages": []},
            "top_genres_overall": {"labels": [], "values": [], "percentages": []},
            "top_movie_genres": {"labels": [], "values": []},
            "top_tv_genres": {"labels": [], "values": []},
            "multi_genre_percentage": 0.0,
            "total_unique_genres": 0
        }

    # 1. Content Type Breakdown
    type_counts = df["type"].value_counts()
    content_type_res = {
        "labels": list(type_counts.index),
        "values": [int(v) for v in type_counts.values],
        "percentages": [round((v / total) * 100, 2) for v in type_counts.values]
    }

    # 2. Overall Genres (Unnested)
    all_genres = get_exploded_series(df, "listed_in")
    top_overall = all_genres.value_counts().head(top_n)
    top_genres_res = {
        "labels": list(top_overall.index),
        "values": [int(v) for v in top_overall.values],
        "percentages": [round((v / total) * 100, 2) for v in top_overall.values]
    }

    # 3. Movie Genres Breakdown
    movie_df = df[df["type"] == "Movie"]
    if not movie_df.empty:
        movie_genres = get_exploded_series(movie_df, "listed_in").value_counts().head(top_n)
        movie_genres_res = {
            "labels": list(movie_genres.index),
            "values": [int(v) for v in movie_genres.values]
        }
    else:
        movie_genres_res = {"labels": [], "values": []}

    # 4. TV Show Genres Breakdown
    tv_df = df[df["type"] == "TV Show"]
    if not tv_df.empty:
        tv_genres = get_exploded_series(tv_df, "listed_in").value_counts().head(top_n)
        tv_genres_res = {
            "labels": list(tv_genres.index),
            "values": [int(v) for v in tv_genres.values]
        }
    else:
        tv_genres_res = {"labels": [], "values": []}

    # 5. Multi-Genre Titles Percentage
    if "genre_count" in df.columns:
        multi_genre_count = int((df["genre_count"] > 1).sum())
        multi_genre_pct = round((multi_genre_count / total) * 100, 2)
    else:
        multi_genre_pct = 0.0

    return {
        "content_type": content_type_res,
        "top_genres_overall": top_genres_res,
        "top_movie_genres": movie_genres_res,
        "top_tv_genres": tv_genres_res,
        "multi_genre_percentage": multi_genre_pct,
        "total_unique_genres": int(all_genres.nunique()) if not all_genres.empty else 0
    }
