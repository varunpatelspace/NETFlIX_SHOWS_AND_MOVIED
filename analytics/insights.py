"""
Rule-Based Insights Engine for Netflix Live Content Analytics Platform.

Generates deterministic, actionable business observations from actual
calculated metrics without Machine Learning or external LLM dependencies.
"""

from typing import List, Dict, Any


def generate_catalog_insights(
    overview: Dict[str, Any],
    content: Dict[str, Any],
    geographic: Dict[str, Any],
    temporal: Dict[str, Any],
    ratings: Dict[str, Any],
    duration: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Synthesize structured analytics metrics into deterministic, human-readable insights.
    
    Args:
        overview: Catalog overview metrics from analytics.overview.
        content: Content type and genre metrics from analytics.content_analysis.
        geographic: Country and co-production metrics from analytics.geographic_analysis.
        temporal: Trend and seasonality metrics from analytics.temporal_analysis.
        ratings: Rating distribution from analytics.rating_analysis.
        duration: Runtime and seasons metrics from analytics.duration_analysis.
        
    Returns:
        List[Dict[str, str]]: Structured insights with category, title, description, and key stat.
    """
    insights: List[Dict[str, str]] = []
    total = overview.get("total_titles", 0)

    if total == 0:
        return [{
            "category": "catalog_status",
            "title": "Empty Catalog",
            "description": "The database currently contains zero records. Run the ETL pipeline to ingest content.",
            "stat": "0 Titles"
        }]

    # 1. Content Mix Insight
    movie_pct = overview.get("movie_percentage", 0.0)
    tv_pct = overview.get("tv_show_percentage", 0.0)
    movies_count = overview.get("movies", 0)
    tv_count = overview.get("tv_shows", 0)
    if movie_pct >= 50.0:
        insights.append({
            "category": "content_mix",
            "title": "Movie Catalog Dominance",
            "description": (
                f"Movies account for {movie_pct}% ({movies_count:,} titles) of the catalog compared to "
                f"{tv_pct}% TV shows ({tv_count:,} titles). Feature film content represents the primary catalog format."
            ),
            "stat": f"{movie_pct}% Movies"
        })
    else:
        insights.append({
            "category": "content_mix",
            "title": "TV Series Catalog Dominance",
            "description": f"TV series account for the majority ({tv_pct}%) of catalog titles.",
            "stat": f"{tv_pct}% TV Shows"
        })

    # 2. Geographic Footprint & Co-Productions
    geo_labels = geographic.get("top_countries_all_credits", {}).get("labels", [])
    geo_pcts = geographic.get("top_countries_all_credits", {}).get("percentages", [])
    co_prod_pct = geographic.get("co_production_percentage", 0.0)
    if geo_labels and geo_pcts:
        top_country = geo_labels[0]
        top_country_pct = geo_pcts[0]
        insights.append({
            "category": "geographic_dominance",
            "title": f"Top Producing Territory: {top_country}",
            "description": (
                f"{top_country} leads all international producing territories, appearing in {top_country_pct}% "
                f"of total title credits. Furthermore, {co_prod_pct}% of catalog titles involve cross-border co-productions."
            ),
            "stat": f"{top_country_pct}% ({top_country})"
        })

    # 3. Top Genre Concentrations
    genre_labels = content.get("top_genres_overall", {}).get("labels", [])
    genre_pcts = content.get("top_genres_overall", {}).get("percentages", [])
    multi_genre_pct = content.get("multi_genre_percentage", 0.0)
    if genre_labels and genre_pcts:
        top_genre = genre_labels[0]
        top_genre_pct = genre_pcts[0]
        insights.append({
            "category": "genre_popularity",
            "title": f"Leading Content Category: {top_genre}",
            "description": (
                f"'{top_genre}' is the most frequent classification, associated with {top_genre_pct}% of titles. "
                f"{multi_genre_pct}% of titles feature multiple genre tags."
            ),
            "stat": f"{top_genre_pct}% ({top_genre})"
        })

    # 4. Target Audience Demographic Skew
    age_labels = ratings.get("age_groups", {}).get("labels", [])
    age_pcts = ratings.get("age_groups", {}).get("percentages", [])
    if age_labels and age_pcts:
        dom_age = age_labels[0]
        dom_age_pct = age_pcts[0]
        insights.append({
            "category": "audience_demographics",
            "title": f"Primary Audience Demographic: {dom_age}",
            "description": (
                f"Catalog maturity certifications show '{dom_age}' as the largest demographic tier, "
                f"comprising {dom_age_pct}% of titles."
            ),
            "stat": f"{dom_age_pct}% {dom_age}"
        })

    # 5. Movie Runtime Distribution
    movie_median = duration.get("movies", {}).get("median_min", 0.0)
    if movie_median > 0:
        insights.append({
            "category": "runtime_optimization",
            "title": "Movie Runtime Median",
            "description": (
                f"Movie runtimes center at a median of {movie_median:.0f} minutes, with the majority of titles "
                "recorded in the standard 90 to 120-minute feature tier."
            ),
            "stat": f"{movie_median:.0f} min median"
        })

    # 6. TV Show Longevity & Season Distribution
    single_season_pct = duration.get("tv_shows", {}).get("single_season_pct", 0.0)
    if single_season_pct > 0:
        insights.append({
            "category": "tv_longevity",
            "title": "Single-Season Concentration",
            "description": (
                f"{single_season_pct}% of television series in the catalog consist of a single season, "
                "with multi-season programs representing the remaining share."
            ),
            "stat": f"{single_season_pct}% Single-Season"
        })

    # 7. Ingestion Seasonality
    monthly = temporal.get("monthly_seasonality", {})
    months = monthly.get("months", [])
    counts = monthly.get("counts", [])
    if months and counts and sum(counts) > 0:
        max_idx = counts.index(max(counts))
        peak_month = months[max_idx]
        peak_count = counts[max_idx]
        insights.append({
            "category": "ingestion_seasonality",
            "title": f"Observed Addition Peak in {peak_month}",
            "description": (
                f"Historical catalog additions peak in {peak_month} with {peak_count:,} titles recorded, "
                "representing the highest monthly addition volume in the dataset."
            ),
            "stat": f"Peak: {peak_month}"
        })

    return insights
