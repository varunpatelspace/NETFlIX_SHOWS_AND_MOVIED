"""
KPI Cards and Freshness Banner Components for Netflix Dashboard.
"""

from typing import Dict, Any
import streamlit as st
from dashboard.components.styling import render_kpi_card


def render_overview_kpi_row(overview: Dict[str, Any]):
    """Render the standard top KPI metric card row."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_kpi_card(
            label="Total Titles",
            value=f"{overview.get('total_titles', 0):,}",
            subtext=f"Span: {overview.get('earliest_release_year', 'N/A')}-{overview.get('latest_release_year', 'N/A')}"
        )
    with col2:
        m_pct = overview.get("movie_percentage", 0.0)
        render_kpi_card(
            label="Movies",
            value=f"{overview.get('movies', 0):,}",
            subtext=f"{m_pct}% of catalog"
        )
    with col3:
        tv_pct = overview.get("tv_show_percentage", 0.0)
        render_kpi_card(
            label="TV Shows",
            value=f"{overview.get('tv_shows', 0):,}",
            subtext=f"{tv_pct}% of catalog"
        )
    with col4:
        render_kpi_card(
            label="Countries",
            value=f"{overview.get('total_countries', 0):,}",
            subtext="Global footprint"
        )
    with col5:
        render_kpi_card(
            label="Unique Genres",
            value=f"{overview.get('total_genres', 0):,}",
            subtext="Content diversity"
        )


def render_freshness_banner(status_data: Dict[str, Any]):
    """Render database status and freshness metadata bar."""
    st.markdown(
        f"""
        <div style="background-color: #1A1A1A; border: 1px solid #2B2B2B; border-radius: 6px; padding: 0.6rem 1rem; margin-top: 2rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; color: #888;">
            <div>
                <span style="color: #46D369; font-weight: 700;">● Live Database</span> | 
                Records: <strong style="color: #fff;">{status_data.get('database_record_count', 0):,}</strong> | 
                Source: <strong style="color: #fff;">{status_data.get('configured_data_source_type', 'CSV').upper()}</strong>
            </div>
            <div>
                Freshness: <strong style="color: #fff;">{status_data.get('latest_database_update_timestamp') or 'Real-time'}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
