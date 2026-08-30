"""
Page 5: Ratings & Audience Demographics Dashboard.
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Community Cloud package resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

st.set_page_config(page_title="Ratings & Demographics | Netflix Analytics", page_icon="🔞", layout="wide")

from dashboard.components import (

    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_section_header,
    plot_vertical_bar,
    plot_donut_chart,
    plot_comparative_bars
)

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">🔞 Ratings & Audience Demographics</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Examine maturity certifications and target audience demographic tiers.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()
with st.spinner("Fetching Ratings & Demographics from API..."):
    ratings_resp = client.get_rating_analysis(filters=filters)

if not ratings_resp["success"]:
    st.error(f"⚠️ **API Error**: {ratings_resp['error']}")
    st.stop()

ratings_data = ratings_resp["data"]
ratings = ratings_data.get("ratings", {})
age_groups = ratings_data.get("age_groups", {})
type_by_rating = ratings_data.get("type_by_rating", {})
dominant_rating = ratings_data.get("dominant_rating", "N/A")
dominant_age = ratings_data.get("dominant_age_group", "N/A")

# Summary KPI Cards
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Dominant Certification</div>
            <div class="netflix-kpi-value">{dominant_rating}</div>
            <div class="netflix-kpi-subtext">Most frequent maturity code</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Primary Audience Tier</div>
            <div class="netflix-kpi-value">{dominant_age}</div>
            <div class="netflix-kpi-subtext">Largest demographic share</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Visualizations
render_section_header("Audience Demographic Breakdown")
col_d1, col_d2 = st.columns([1, 1])

with col_d1:
    if age_groups.get("labels"):
        st.plotly_chart(
            plot_donut_chart(age_groups["labels"], age_groups["values"], title="5-Tier Audience Demographics"),
            width="stretch"
        )
    else:
        st.info("No demographic records matching filter.")

with col_d2:
    if ratings.get("labels"):
        st.plotly_chart(
            plot_vertical_bar(ratings["labels"][:10], ratings["values"][:10], title="Top 10 Certification Codes"),
            width="stretch"
        )
    else:
        st.info("No certification records matching filter.")

# Cross-Tabulation: Content Type by Rating
render_section_header("Format Certification Split: Movies vs TV Series")
if type_by_rating.get("ratings"):
    st.plotly_chart(
        plot_comparative_bars(
            categories=type_by_rating["ratings"],
            series_a=type_by_rating["movies"],
            series_b=type_by_rating["tv_shows"],
            name_a="Movies",
            name_b="TV Shows",
            title="Content Volume by Maturity Rating and Format"
        ),
        width="stretch"
    )
