"""
Page 6: Runtime & Season Longevity Analysis Dashboard.
"""

import streamlit as st

st.set_page_config(page_title="Duration & Longevity | Netflix Analytics", page_icon="⏱️", layout="wide")

from dashboard.components import (
    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_section_header,
    plot_vertical_bar
)

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">⏱️ Duration & Season Longevity</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Explore movie runtime distributions and television series season longevity.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()
with st.spinner("Fetching Duration Metrics from API..."):
    dur_resp = client.get_duration_analysis(filters=filters)

if not dur_resp["success"]:
    st.error(f"⚠️ **API Error**: {dur_resp['error']}")
    st.stop()

dur_data = dur_resp["data"]
movies = dur_data.get("movies", {})
tv = dur_data.get("tv_shows", {})

# -----------------------------------------------------------------------------
# 1. MOVIE RUNTIME ANALYSIS
# -----------------------------------------------------------------------------
render_section_header("Feature Film Runtimes (Minutes)")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Average Runtime</div>
            <div class="netflix-kpi-value">{movies.get('mean_min', 0.0)} <span style="font-size:1rem;color:#888;">min</span></div>
            <div class="netflix-kpi-subtext">Mean movie length</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with m_col2:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Median Runtime</div>
            <div class="netflix-kpi-value">{movies.get('median_min', 0.0)} <span style="font-size:1rem;color:#888;">min</span></div>
            <div class="netflix-kpi-subtext">50th percentile sweet spot</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with m_col3:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Shortest Movie</div>
            <div class="netflix-kpi-value">{movies.get('min_min', 0.0)} <span style="font-size:1rem;color:#888;">min</span></div>
            <div class="netflix-kpi-subtext">Minimum recorded runtime</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with m_col4:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Longest Movie</div>
            <div class="netflix-kpi-value">{movies.get('max_min', 0.0)} <span style="font-size:1rem;color:#888;">min</span></div>
            <div class="netflix-kpi-subtext">Maximum recorded runtime</div>
        </div>
        """,
        unsafe_allow_html=True
    )

tiers = movies.get("duration_tiers", {})
if tiers.get("labels"):
    st.plotly_chart(
        plot_vertical_bar(tiers["labels"], tiers["values"], title="Movie Duration Categorical Tiers", color="#E50914"),
        width="stretch"
    )

# -----------------------------------------------------------------------------
# 2. TV SHOW SEASONS ANALYSIS
# -----------------------------------------------------------------------------
render_section_header("Television Series Longevity (Seasons)")

tv_col1, tv_col2, tv_col3, tv_col4 = st.columns(4)
with tv_col1:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Average Seasons</div>
            <div class="netflix-kpi-value">{tv.get('mean_seasons', 0.0)}</div>
            <div class="netflix-kpi-subtext">Mean seasons per series</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with tv_col2:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Single-Season Rate</div>
            <div class="netflix-kpi-value">{tv.get('single_season_pct', 0.0)}%</div>
            <div class="netflix-kpi-subtext">Series with only 1 season</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with tv_col3:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">3+ Seasons Franchise</div>
            <div class="netflix-kpi-value">{tv.get('three_plus_seasons_pct', 0.0)}%</div>
            <div class="netflix-kpi-subtext">Long-running programs</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with tv_col4:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Maximum Seasons</div>
            <div class="netflix-kpi-value">{tv.get('max_seasons', 0)}</div>
            <div class="netflix-kpi-subtext">Longest running series</div>
        </div>
        """,
        unsafe_allow_html=True
    )

season_dist = tv.get("season_distribution", {})
if season_dist.get("labels"):
    st.plotly_chart(
        plot_vertical_bar(season_dist["labels"], season_dist["values"], title="TV Show Season Distribution (Seasons 1 - 10)", color="#B81D24"),
        width="stretch"
    )
