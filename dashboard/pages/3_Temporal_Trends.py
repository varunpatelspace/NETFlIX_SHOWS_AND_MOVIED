"""
Page 3: Temporal Trends & Ingestion Seasonality Dashboard.
"""

import streamlit as st

st.set_page_config(page_title="Temporal Trends | Netflix Analytics", page_icon="📈", layout="wide")

from dashboard.components import (
    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_section_header,
    plot_line_chart,
    plot_vertical_bar,
    plot_comparative_bars
)

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">📈 Temporal Trends & Ingestion Dynamics</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Track multi-year catalog expansion, monthly ingestion peaks, and licensing delays.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()
with st.spinner("Loading Temporal Trends from API..."):
    temporal_resp = client.get_temporal_analysis(filters=filters)

if not temporal_resp["success"]:
    st.error(f"⚠️ **API Error**: {temporal_resp['error']}")
    st.stop()

temporal = temporal_resp["data"]
yearly_add = temporal.get("yearly_additions", {})
yearly_rel = temporal.get("yearly_releases", {})
monthly = temporal.get("monthly_seasonality", {})
lag_stats = temporal.get("licensing_lag_stats", {})
comp = temporal.get("comparative_yearly", {})

# 1. Yearly Ingestion vs Release Trajectories
col1, col2 = st.columns(2)

with col1:
    if yearly_add.get("years"):
        st.plotly_chart(
            plot_line_chart(yearly_add["years"], yearly_add["counts"], title="Catalog Additions by Year (Ingestion Volume)"),
            width="stretch"
        )
    else:
        st.info("No yearly addition records matching filter.")

with col2:
    if yearly_rel.get("years"):
        st.plotly_chart(
            plot_line_chart(yearly_rel["years"], yearly_rel["counts"], title="Content Premiere Release Year Distribution (Modern Era)", line_color="#E5A914"),
            width="stretch"
        )
    else:
        st.info("No release year records matching filter.")

# 2. Comparative Additions: Movies vs TV Shows
render_section_header("Comparative Format Growth: Movies vs TV Series")

if comp.get("years"):
    st.plotly_chart(
        plot_comparative_bars(
            categories=comp["years"],
            series_a=comp["movies"],
            series_b=comp["tv_shows"],
            name_a="Movies Added",
            name_b="TV Shows Added",
            title="Annual Ingestion Comparison by Format"
        ),
        width="stretch"
    )

# 3. Seasonality & Licensing Lag
render_section_header("Ingestion Seasonality & Licensing Latency")
col_s1, col_s2 = st.columns([2, 1])

with col_s1:
    if monthly.get("months"):
        st.plotly_chart(
            plot_vertical_bar(monthly["months"], monthly["counts"], title="Monthly Ingestion Seasonality (January - December)", color="#B81D24"),
            width="stretch"
        )

with col_s2:
    st.markdown(
        f"""
        <div style="background-color: #1F1F1F; border: 1px solid #2E2E2E; border-radius: 8px; padding: 1.5rem; margin-top: 3.5rem;">
            <div style="color: #888; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Median Licensing Lag</div>
            <div style="color: #fff; font-size: 2.2rem; font-weight: 800; margin: 0.5rem 0;">{lag_stats.get('median_lag_years', 0.0)} Years</div>
            <div style="color: #aaa; font-size: 0.85rem;">Time from original theatrical/broadcast premiere to Netflix catalog addition</div>
            <hr style="border-color: #333; margin: 1rem 0;">
            <div style="color: #888; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Same-Year Ingestion</div>
            <div style="color: #46D369; font-size: 2.0rem; font-weight: 800; margin: 0.5rem 0;">{lag_stats.get('same_year_release_pct', 0.0)}%</div>
            <div style="color: #aaa; font-size: 0.85rem;">Titles licensed and added in their premiere release year</div>
        </div>
        """,
        unsafe_allow_html=True
    )
