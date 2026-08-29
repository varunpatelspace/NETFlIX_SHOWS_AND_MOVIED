"""
Exploratory Data Analysis (EDA) Module for Netflix Movies and TV Shows.

This module computes detailed statistical summaries and analytical tables across
all 10 project dimensions:
    A. Content Type Analysis
    B. Country Analysis
    C. Genre Analysis
    D. Time & Trend Analysis
    E. Rating & Audience Demographics
    F. Director Analysis
    G. Cast Analysis
    H. Movie Duration Analysis
    I. TV Show Seasons Analysis
    J. Comparative Cross-Tabulation Analysis
"""

import os
import sys

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
import numpy as np
from src.data_cleaning import load_dataset, get_exploded_series, get_movies_df, get_tvshows_df


def analyze_content_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze the distribution of Movies vs TV Shows.
    
    Returns:
        pd.DataFrame: Counts, percentages, and catalog ratios.
    """
    summary = df["type"].value_counts().reset_index()
    summary.columns = ["type", "count"]
    summary["percentage"] = (summary["count"] / len(df) * 100).round(2)
    return summary


def analyze_countries(df: pd.DataFrame, top_n: int = 15) -> dict:
    """
    Analyze geographic production of content.
    
    Computes:
        - Top countries across all production credits (unnested)
        - Top primary producing countries
        - Proportion of international co-productions
    
    Returns:
        dict: Top unnested countries, primary countries, and co-production stats.
    """
    all_countries = get_exploded_series(df, "country")
    top_all = all_countries.value_counts().head(top_n).reset_index()
    top_all.columns = ["country", "title_count"]
    top_all["percentage_of_catalog"] = (top_all["title_count"] / len(df) * 100).round(2)
    
    # Primary country breakdown
    primary_counts = df[df["primary_country"] != "Unknown Country"]["primary_country"].value_counts().head(top_n).reset_index()
    primary_counts.columns = ["primary_country", "title_count"]
    
    # Co-production statistics
    multi_country_pct = (df["is_multi_country"].sum() / len(df) * 100).round(2)
    
    return {
        "top_countries_all_credits": top_all,
        "top_primary_countries": primary_counts,
        "co_production_percentage": multi_country_pct
    }


def analyze_genres(df: pd.DataFrame, top_n: int = 15) -> dict:
    """
    Analyze genre and category distribution globally and by content type.
    
    Returns:
        dict: Top overall genres, movie genres, and TV show genres.
    """
    # Overall genres
    all_genres = get_exploded_series(df, "listed_in")
    top_genres = all_genres.value_counts().head(top_n).reset_index()
    top_genres.columns = ["genre", "count"]
    top_genres["percentage"] = (top_genres["count"] / len(df) * 100).round(2)
    
    # Movie genres
    movies_df = get_movies_df(df)
    movie_genres = get_exploded_series(movies_df, "listed_in").value_counts().head(top_n).reset_index()
    movie_genres.columns = ["genre", "count"]
    
    # TV Show genres
    tv_df = get_tvshows_df(df)
    tv_genres = get_exploded_series(tv_df, "listed_in").value_counts().head(top_n).reset_index()
    tv_genres.columns = ["genre", "count"]
    
    return {
        "top_genres_overall": top_genres,
        "top_movie_genres": movie_genres,
        "top_tv_genres": tv_genres,
        "total_unique_genres": all_genres.nunique()
    }


def analyze_temporal_trends(df: pd.DataFrame) -> dict:
    """
    Analyze content growth by release year and Netflix addition year, plus monthly seasonality.
    
    Returns:
        dict: Release year trends, addition year trends, monthly additions, and licensing lag.
    """
    # Content additions by year
    added_yearly = df["year_added"].dropna().value_counts().sort_index().reset_index()
    added_yearly.columns = ["year_added", "titles_added"]
    added_yearly["year_added"] = added_yearly["year_added"].astype(int)
    added_yearly["growth_rate_pct"] = (added_yearly["titles_added"].pct_change() * 100).round(2)
    
    # Content by release year (last 25 years focus)
    release_yearly = df[df["release_year"] >= 1995]["release_year"].value_counts().sort_index().reset_index()
    release_yearly.columns = ["release_year", "titles_released"]
    
    # Monthly additions seasonality
    months_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    monthly = df["month_name_added"].dropna().value_counts().reindex(months_order).reset_index()
    monthly.columns = ["month", "titles_added"]
    monthly["percentage"] = (monthly["titles_added"] / monthly["titles_added"].sum() * 100).round(2)
    
    # Licensing lag statistics (years from release to Netflix catalog entry)
    lag_valid = df["release_to_add_lag"].dropna()
    lag_stats = {
        "mean_lag_years": round(float(lag_valid.mean()), 2),
        "median_lag_years": round(float(lag_valid.median()), 2),
        "same_year_release_pct": round(float((lag_valid <= 0).mean() * 100), 2),
        "within_2_years_pct": round(float((lag_valid <= 2).mean() * 100), 2)
    }
    
    return {
        "yearly_additions": added_yearly,
        "yearly_releases": release_yearly,
        "monthly_additions": monthly,
        "licensing_lag_stats": lag_stats
    }


def analyze_ratings_and_demographics(df: pd.DataFrame) -> dict:
    """
    Analyze age ratings and demographic tier distribution across content types.
    
    Returns:
        dict: Overall rating counts, grouped rating breakdown by type, and demographic tiers.
    """
    # Raw rating breakdown
    rating_counts = df["rating"].value_counts().reset_index()
    rating_counts.columns = ["rating", "count"]
    rating_counts["percentage"] = (rating_counts["count"] / len(df) * 100).round(2)
    
    # Cross-tabulation: Rating vs Type
    rating_by_type = pd.crosstab(df["rating"], df["type"], margins=True).sort_values("All", ascending=False)
    
    # Demographic age groups
    demographics = df["age_group"].value_counts().reset_index()
    demographics.columns = ["age_group", "count"]
    demographics["percentage"] = (demographics["count"] / len(df) * 100).round(2)
    
    demo_by_type = pd.crosstab(df["age_group"], df["type"], normalize="columns").round(4) * 100
    
    return {
        "rating_counts": rating_counts,
        "rating_by_type": rating_by_type,
        "demographics": demographics,
        "demographics_by_type_pct": demo_by_type
    }


def analyze_directors(df: pd.DataFrame, top_n: int = 15) -> dict:
    """
    Analyze top content creators and directors.
    
    Returns:
        dict: Top directors overall, top movie directors, and collaborative director counts.
    """
    all_directors = get_exploded_series(df, "director")
    top_directors = all_directors.value_counts().head(top_n).reset_index()
    top_directors.columns = ["director", "title_count"]
    
    # Movie directors
    movies_df = get_movies_df(df)
    movie_directors = get_exploded_series(movies_df, "director").value_counts().head(top_n).reset_index()
    movie_directors.columns = ["director", "title_count"]
    
    return {
        "top_directors_overall": top_directors,
        "top_movie_directors": movie_directors,
        "total_unique_directors": all_directors.nunique()
    }


def analyze_cast(df: pd.DataFrame, top_n: int = 15) -> dict:
    """
    Analyze actor appearances globally and by major country markets.
    
    Returns:
        dict: Top actors globally, in India, in US, and in UK.
    """
    all_cast = get_exploded_series(df, "cast")
    top_cast = all_cast.value_counts().head(top_n).reset_index()
    top_cast.columns = ["actor", "appearances"]
    
    # Regional breakdown for top 3 markets
    # India
    india_df = df[df["country"].str.contains("India", na=False)]
    top_india = get_exploded_series(india_df, "cast").value_counts().head(top_n).reset_index()
    top_india.columns = ["actor", "appearances"]
    
    # United States
    us_df = df[df["country"].str.contains("United States", na=False)]
    top_us = get_exploded_series(us_df, "cast").value_counts().head(top_n).reset_index()
    top_us.columns = ["actor", "appearances"]
    
    return {
        "top_actors_global": top_cast,
        "top_actors_india": top_india,
        "top_actors_us": top_us,
        "total_unique_actors": all_cast.nunique()
    }


def analyze_movie_durations(df: pd.DataFrame) -> dict:
    """
    Analyze movie runtimes (in minutes), outliers, and runtime tiers.
    
    Returns:
        dict: Summary statistics, longest movies, shortest movies, and duration tier distribution.
    """
    movies_df = get_movies_df(df)
    durations = movies_df["duration_min"].dropna()
    
    stats = {
        "count": int(durations.count()),
        "mean_min": round(float(durations.mean()), 2),
        "median_min": round(float(durations.median()), 2),
        "std_min": round(float(durations.std()), 2),
        "min_min": float(durations.min()),
        "max_min": float(durations.max()),
        "q25_min": float(durations.quantile(0.25)),
        "q75_min": float(durations.quantile(0.75)),
        "iqr_min": float(durations.quantile(0.75) - durations.quantile(0.25))
    }
    
    # Top 5 longest movies
    longest = movies_df.sort_values("duration_min", ascending=False)[
        ["title", "release_year", "primary_country", "duration_min"]
    ].head(5)
    
    # Top 5 shortest movies (excluding 0)
    shortest = movies_df[movies_df["duration_min"] > 0].sort_values("duration_min", ascending=True)[
        ["title", "release_year", "primary_country", "duration_min"]
    ].head(5)
    
    # Tier breakdown
    tier_dist = movies_df["movie_duration_tier"].value_counts().reset_index()
    tier_dist.columns = ["tier", "count"]
    tier_dist["percentage"] = (tier_dist["count"] / len(movies_df) * 100).round(2)
    
    return {
        "duration_stats": stats,
        "longest_movies": longest,
        "shortest_movies": shortest,
        "duration_tiers": tier_dist
    }


def analyze_tv_shows(df: pd.DataFrame) -> dict:
    """
    Analyze TV show season lengths, renewal patterns, and longest-running titles.
    
    Returns:
        dict: Season count distribution, single-season proportion, and top longest running shows.
    """
    tv_df = get_tvshows_df(df)
    seasons = tv_df["seasons"].dropna()
    
    season_counts = seasons.value_counts().sort_index().reset_index()
    season_counts.columns = ["seasons", "count"]
    season_counts["percentage"] = (season_counts["count"] / len(tv_df) * 100).round(2)
    
    single_season_pct = round(float((seasons == 1).mean() * 100), 2)
    two_season_pct = round(float((seasons == 2).mean() * 100), 2)
    three_plus_pct = round(float((seasons >= 3).mean() * 100), 2)
    
    # Longest running shows
    longest_shows = tv_df.sort_values("seasons", ascending=False)[
        ["title", "release_year", "primary_country", "seasons"]
    ].head(10)
    
    return {
        "season_distribution": season_counts,
        "single_season_pct": single_season_pct,
        "two_season_pct": two_season_pct,
        "three_plus_seasons_pct": three_plus_pct,
        "longest_running_shows": longest_shows
    }


def analyze_comparative(df: pd.DataFrame) -> dict:
    """
    Cross-tabulate Movies vs TV Shows across countries, ratings, and time.
    
    Returns:
        dict: Pivot tables of Type vs Country, Type vs Rating, and Type vs Year Added.
    """
    # 1. Type across top countries
    top_country_names = df[df["primary_country"] != "Unknown Country"]["primary_country"].value_counts().head(10).index
    country_type = pd.crosstab(
        df[df["primary_country"].isin(top_country_names)]["primary_country"],
        df["type"]
    ).loc[top_country_names]
    country_type["Total"] = country_type.sum(axis=1)
    country_type["Movie_Pct"] = (country_type["Movie"] / country_type["Total"] * 100).round(1)
    country_type["TV_Pct"] = (country_type["TV Show"] / country_type["Total"] * 100).round(1)
    
    # 2. Type across ratings
    rating_type = pd.crosstab(df["rating"], df["type"])
    
    # 3. Type growth over time (year_added >= 2012)
    yearly_df = df[df["year_added"] >= 2012].dropna(subset=["year_added"])
    yearly_type = pd.crosstab(yearly_df["year_added"].astype(int), yearly_df["type"])
    yearly_type["Total"] = yearly_type.sum(axis=1)
    yearly_type["Movie_Share"] = (yearly_type["Movie"] / yearly_type["Total"] * 100).round(1)
    yearly_type["TV_Share"] = (yearly_type["TV Show"] / yearly_type["Total"] * 100).round(1)
    
    return {
        "country_vs_type": country_type,
        "rating_vs_type": rating_type,
        "year_vs_type": yearly_type
    }


def run_full_eda(data_path: str = "data/netflix_cleaned.csv") -> dict:
    """
    Execute full suite of EDA analyses and log consolidated report to console.
    
    Returns:
        dict: All analysis results structured by domain.
    """
    if not os.path.exists(data_path):
        from src.data_cleaning import clean_netflix_pipeline
        clean_netflix_pipeline()
        
    df = pd.read_csv(data_path)
    
    results = {
        "content_type": analyze_content_type(df),
        "countries": analyze_countries(df),
        "genres": analyze_genres(df),
        "temporal": analyze_temporal_trends(df),
        "ratings": analyze_ratings_and_demographics(df),
        "directors": analyze_directors(df),
        "cast": analyze_cast(df),
        "movie_duration": analyze_movie_durations(df),
        "tv_shows": analyze_tv_shows(df),
        "comparative": analyze_comparative(df)
    }
    
    print("\n" + "=" * 70)
    print("NETFLIX EXPLORATORY DATA ANALYSIS KEY HIGHLIGHTS")
    print("=" * 70)
    
    # Print A. Content Type
    print("\n[A] CONTENT TYPE BREAKDOWN:")
    print(results["content_type"].to_string(index=False))
    
    # Print B. Countries
    print("\n[B] TOP 5 CONTENT PRODUCING COUNTRIES:")
    print(results["countries"]["top_countries_all_credits"].head(5).to_string(index=False))
    print(f"International Co-productions: {results['countries']['co_production_percentage']}%")
    
    # Print C. Genres
    print("\n[C] TOP 5 GENRES GLOBALLY:")
    print(results["genres"]["top_genres_overall"].head(5).to_string(index=False))
    
    # Print D. Time
    print("\n[D] RECENT YEAR ADDITIONS & GROWTH:")
    print(results["temporal"]["yearly_additions"].tail(5).to_string(index=False))
    print(f"Median licensing lag from release to catalog: {results['temporal']['licensing_lag_stats']['median_lag_years']} years")
    
    # Print E. Ratings
    print("\n[E] TARGET AUDIENCE DEMOGRAPHICS:")
    print(results["ratings"]["demographics"].to_string(index=False))
    
    # Print H. Duration
    print("\n[H] MOVIE RUNTIME SUMMARY (MINUTES):")
    for k, v in results["movie_duration"]["duration_stats"].items():
        print(f"  {k:<15}: {v}")
        
    # Print I. TV Shows
    print(f"\n[I] TV SHOWS: Single-Season Shows: {results['tv_shows']['single_season_pct']}% | 3+ Seasons: {results['tv_shows']['three_plus_seasons_pct']}%")
    
    print("=" * 70 + "\n")
    return results


if __name__ == "__main__":
    run_full_eda()
