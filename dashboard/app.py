"""
Main Application Entrypoint for Netflix Live Content Analytics Streamlit Dashboard.
Executive Overview Dashboard consuming the FastAPI backend.
"""

import streamlit as st

st.set_page_config(
    page_title="Netflix Live Content Analytics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)
import os

import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Community Cloud deployment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components import (

    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_overview_kpi_row,
    render_section_header,
    render_insight_card,
    render_freshness_banner,
    plot_donut_chart,
    plot_line_chart,
    plot_horizontal_bar
)

# Apply custom Netflix theme and layout
apply_netflix_theme()

# Global Sidebar Filters
filters = render_sidebar_filters()

# Header Banner
st.markdown('<div class="netflix-brand-title">🎬 Netflix Movies & Shows Analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="netflix-brand-subtitle">Executive catalog intelligence, demographic ratings, and automated content updates.</div>',
    unsafe_allow_html=True
)

render_active_filters_banner(filters)

# Fetch Dashboard Data via API Client
client = ApiClient()

with st.spinner("Connecting to Netflix Live Analytics API..."):
    resp = client.get_dashboard_summary(filters=filters)
    status_resp = client.get_pipeline_status()

if not resp["success"]:
    st.error(f"⚠️ **API Unavailable**: {resp['error']}")
    st.markdown(f"**Targeted Backend URL:** `{client.base_url}`")
    st.info(
        "💡 **Connection Guidance:**\n\n"
        "- **Local Run**: Launch the FastAPI backend via: `uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload`\n"
        "- **Cloud Deployment**: Ensure the environment variable or Streamlit secret `API_BASE_URL` points to your public FastAPI server (e.g. `https://<your-service>.onrender.com`)."
    )
    st.stop()

data = resp["data"]
overview = data.get("overview", {})
content = data.get("content", {})
temporal = data.get("temporal", {})
geographic = data.get("geographic", {})
insights = data.get("insights", [])
pipeline_status = status_resp.get("data", {}) if status_resp.get("success") else {}

# -----------------------------------------------------------------------------
# 1. High-Level KPI Cards
# -----------------------------------------------------------------------------
render_overview_kpi_row(overview)

# -----------------------------------------------------------------------------
# 2. Main Executive Charts (Grid Row 1)
# -----------------------------------------------------------------------------
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    type_data = content.get("content_type", {})
    if type_data.get("labels"):
        fig_donut = plot_donut_chart(
            labels=type_data["labels"],
            values=type_data["values"],
            title="Catalog Composition: Movies vs TV Shows"
        )
        st.plotly_chart(fig_donut, width="stretch")
    else:
        st.info("No content format records matching current filters.")

with col_chart2:
    yearly_data = temporal.get("yearly_additions", {})
    if yearly_data.get("years"):
        fig_growth = plot_line_chart(
            x=yearly_data["years"],
            y=yearly_data["counts"],
            title="Content Ingestion Trajectory (Titles Added by Year)"
        )
        st.plotly_chart(fig_growth, width="stretch")
    else:
        st.info("No temporal records matching current filters.")

# -----------------------------------------------------------------------------
# 3. Secondary Distributions (Grid Row 2)
# -----------------------------------------------------------------------------
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    genre_data = content.get("top_genres_overall", {})
    if genre_data.get("labels"):
        fig_genres = plot_horizontal_bar(
            labels=genre_data["labels"][:10],
            values=genre_data["values"][:10],
            title="Top 10 Global Content Classifications"
        )
        st.plotly_chart(fig_genres, width="stretch")

with col_chart4:
    geo_data = geographic.get("top_countries_all_credits", {})
    if geo_data.get("labels"):
        fig_geo = plot_horizontal_bar(
            labels=geo_data["labels"][:10],
            values=geo_data["values"][:10],
            title="Top 10 Content Producing Territories",
            color="#991419"
        )
        st.plotly_chart(fig_geo, width="stretch")

# -----------------------------------------------------------------------------
# 4. Evidence-Based Insights Section
# -----------------------------------------------------------------------------
render_section_header("Evidence-Based Business Observations")

if insights:
    ins_col1, ins_col2 = st.columns(2)
    for idx, item in enumerate(insights):
        target_col = ins_col1 if idx % 2 == 0 else ins_col2
        with target_col:
            render_insight_card(
                title=item.get("title", ""),
                description=item.get("description", ""),
                category=item.get("category", ""),
                stat=item.get("stat", "")
            )
else:
    st.info("No observations generated for current filter criteria.")

# -----------------------------------------------------------------------------
# 5. Data Freshness Status Bar
# -----------------------------------------------------------------------------
render_freshness_banner(pipeline_status)
