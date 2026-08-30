"""
Geographic Analytics Module for Netflix Live Content Analytics Platform.

Analyzes content production footprints across countries and international co-productions.
"""

from typing import Dict, Any
import pandas as pd
from src.data_cleaning import get_exploded_series


def get_geographic_analysis(df: pd.DataFrame, top_n: int = 15) -> Dict[str, Any]:
    """
    Compute geographic distribution, producing hubs, and co-production metrics.
    
    Args:
        df: Filtered catalog DataFrame from repository.
        top_n: Number of top countries to return.
        
    Returns:
        Dict[str, Any]: Top producing countries (all production credits),
                        top primary producing countries, and co-production statistics.
    """
    total = len(df)
    if total == 0:
        return {
            "top_countries_all_credits": {"labels": [], "values": [], "percentages": []},
            "top_primary_countries": {"labels": [], "values": []},
            "co_production_count": 0,
            "co_production_percentage": 0.0,
            "single_country_percentage": 0.0,
            "total_countries_represented": 0
        }

    # 1. All Production Credits (Unnested multi-country credits)
    all_countries = get_exploded_series(df, "country")
    top_all = all_countries.value_counts().head(top_n)
    top_all_res = {
        "labels": list(top_all.index),
        "values": [int(v) for v in top_all.values],
        "percentages": [round((v / total) * 100, 2) for v in top_all.values]
    }

    # 2. Primary Producing Country Breakdown
    if "primary_country" in df.columns:
        primary_valid = df[df["primary_country"].notnull() & (df["primary_country"] != "Unknown Country")]
        top_primary = primary_valid["primary_country"].value_counts().head(top_n)
        top_primary_res = {
            "labels": list(top_primary.index),
            "values": [int(v) for v in top_primary.values]
        }
    else:
        top_primary_res = {"labels": [], "values": []}

    # 3. International Co-productions
    if "is_multi_country" in df.columns:
        co_prod_count = int(df["is_multi_country"].sum())
        co_prod_pct = round((co_prod_count / total) * 100, 2)
        single_prod_pct = round(100.0 - co_prod_pct, 2)
    else:
        co_prod_count = 0
        co_prod_pct = 0.0
        single_prod_pct = 100.0

    return {
        "top_countries_all_credits": top_all_res,
        "top_primary_countries": top_primary_res,
        "co_production_count": co_prod_count,
        "co_production_percentage": co_prod_pct,
        "single_country_percentage": single_prod_pct,
        "total_countries_represented": int(all_countries.nunique()) if not all_countries.empty else 0
    }
