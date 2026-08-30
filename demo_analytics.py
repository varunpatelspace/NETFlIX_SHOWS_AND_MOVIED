"""
Demonstration script for Phase 5: Database-Driven Analytics Engine.
Queries the database repository and prints live calculated metrics and insights.
"""

from database.database import SessionLocal
from analytics.analytics_service import AnalyticsService


def main():
    session = SessionLocal()
    service = AnalyticsService(session)

    ov = service.get_overview()
    content = service.get_content_analysis(top_n=10)
    geo = service.get_geographic_analysis(top_n=10)
    temporal = service.get_temporal_analysis()
    ratings = service.get_rating_analysis()
    duration = service.get_duration_analysis()
    insights = service.get_all_insights()

    print("\n" + "=" * 70)
    print("  NETFLIX LIVE CONTENT ANALYTICS ENGINE — LIVE DATABASE DEMONSTRATION")
    print("=" * 70)

    print("\n[1] CATALOG OVERVIEW:")
    print(f"  Total Titles:          {ov['total_titles']:,}")
    print(f"  Movies:                {ov['movies']:,} ({ov['movie_percentage']}%)")
    print(f"  TV Shows:              {ov['tv_shows']:,} ({ov['tv_show_percentage']}%)")
    print(f"  Release Year Span:     {ov['earliest_release_year']} - {ov['latest_release_year']} (Avg: {ov['average_release_year']})")
    print(f"  Countries Represented: {ov['total_countries']}")
    print(f"  Unique Genres:         {ov['total_genres']}")
    print(f"  DB Freshness:          {ov['database_freshness']}")

    print("\n[2] TOP 10 CONTENT PRODUCING COUNTRIES:")
    for c, v, p in zip(geo["top_countries_all_credits"]["labels"], geo["top_countries_all_credits"]["values"], geo["top_countries_all_credits"]["percentages"]):
        print(f"  - {c:<20}: {v:>5,} titles ({p:>5.1f}%)")
    print(f"  International Co-productions: {geo['co_production_percentage']}%")

    print("\n[3] TOP 10 GENRES GLOBALLY:")
    for g, v, p in zip(content["top_genres_overall"]["labels"], content["top_genres_overall"]["values"], content["top_genres_overall"]["percentages"]):
        print(f"  - {g:<25}: {v:>5,} titles ({p:>5.1f}%)")

    print("\n[4] RECENT RELEASE YEAR TREND (LAST 5 YEARS):")
    for y, v in list(zip(temporal["yearly_releases"]["years"], temporal["yearly_releases"]["counts"]))[-5:]:
        print(f"  - Year {y}: {v:>5,} titles released")

    print("\n[5] CONTENT RATING DISTRIBUTION (TOP 5):")
    for r, v, p in list(zip(ratings["ratings"]["labels"], ratings["ratings"]["values"], ratings["ratings"]["percentages"]))[:5]:
        print(f"  - {r:<10}: {v:>5,} titles ({p:>5.1f}%)")

    print("\n[6] RUNTIME & LONGEVITY:")
    print(f"  Average Movie Duration:  {duration['movies']['mean_min']} min (Median: {duration['movies']['median_min']} min, Range: {duration['movies']['min_min']} - {duration['movies']['max_min']} min)")
    print(f"  Average TV Show Seasons: {duration['tv_shows']['mean_seasons']} (Max: {duration['tv_shows']['max_seasons']}, Single-Season: {duration['tv_shows']['single_season_pct']}%, 3+ Seasons: {duration['tv_shows']['three_plus_seasons_pct']}%)")

    print("\n[7] AUTOMATICALLY GENERATED DETERMINISTIC INSIGHTS:")
    for i, ins in enumerate(insights, 1):
        print(f"  {i}. [{ins['category'].upper()}] {ins['title']}")
        print(f"     \"{ins['description']}\" (Stat: {ins['stat']})")

    print("\n" + "=" * 70 + "\n")
    session.close()


if __name__ == "__main__":
    main()
