"""
Page 2: Content Format & Genre Analysis Dashboard.
"""

import streamlit as st

st.set_page_config(page_title="Content Analysis | Netflix Analytics", page_icon="🎭", layout="wide")

from dashboard.components import (
    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_section_header,
    plot_donut_chart,
    plot_horizontal_bar,
    plot_vertical_bar
)

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">🎭 Content & Genre Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Deep-dive into catalog classifications, formats, and genre combinations.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()
with st.spinner("Fetching Content Analysis from API..."):
    content_resp = client.get_content_analysis(filters=filters)
    ratings_resp = client.get_rating_analysis(filters=filters)

if not content_resp["success"]:
    st.error(f"⚠️ **API Error**: {content_resp['error']}")
    st.stop()

content = content_resp["data"]
ratings = ratings_resp.get("data", {}) if ratings_resp.get("success") else {}

# Top Summary Row
col1, col2 = st.columns(2)
with col1:
    type_data = content.get("content_type", {})
    if type_data.get("labels"):
        st.plotly_chart(
            plot_donut_chart(type_data["labels"], type_data["values"], title="Content Formats: Movies vs TV Shows"),
            use_container_width=True
        )
    else:
        st.info("No content format records matching filter.")

with col2:
    genres = content.get("top_genres_overall", {})
    if genres.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(genres["labels"][:12], genres["values"][:12], title="Top 12 Overall Genre Categories"),
            use_container_width=True
        )
    else:
        st.info("No genre records matching filter.")

# Multi-Genre Breakdown
render_section_header("Genre Specialization: Movies vs TV Series")

col_m, col_tv = st.columns(2)
with col_m:
    m_genres = content.get("top_movie_genres", {})
    if m_genres.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(m_genres["labels"][:10], m_genres["values"][:10], title="Top 10 Movie Genres", color="#E50914"),
            use_container_width=True
        )
    else:
        st.info("No movie genre records matching filter.")

with col_tv:
    tv_genres = content.get("top_tv_genres", {})
    if tv_genres.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(tv_genres["labels"][:10], tv_genres["values"][:10], title="Top 10 TV Show Genres", color="#B81D24"),
            use_container_width=True
        )
    else:
        st.info("No TV genre records matching filter.")

# Certification Distribution
render_section_header("Content Certification & Multi-Genre Share")
c_cert1, c_cert2 = st.columns([2, 1])

with c_cert1:
    rating_data = ratings.get("ratings", {})
    if rating_data.get("labels"):
        st.plotly_chart(
            plot_vertical_bar(rating_data["labels"][:10], rating_data["values"][:10], title="Top 10 Maturity Certification Codes"),
            use_container_width=True
        )

with c_cert2:
    st.markdown(
        f"""
        <div style="background-color: #1F1F1F; border: 1px solid #2E2E2E; border-radius: 8px; padding: 1.5rem; margin-top: 3.5rem;">
            <div style="color: #888; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Hybrid Categorization</div>
            <div style="color: #fff; font-size: 2.2rem; font-weight: 800; margin: 0.5rem 0;">{content.get('multi_genre_percentage', 0.0)}%</div>
            <div style="color: #46D369; font-size: 0.85rem;">Titles tagged with 2 or more genre labels</div>
            <hr style="border-color: #333; margin: 1rem 0;">
            <div style="color: #888; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Unique Classifications</div>
            <div style="color: #fff; font-size: 2.0rem; font-weight: 800; margin: 0.5rem 0;">{content.get('total_unique_genres', 0)}</div>
            <div style="color: #aaa; font-size: 0.85rem;">Total distinct genre tags globally</div>
        </div>
        """,
        unsafe_allow_html=True
    )
