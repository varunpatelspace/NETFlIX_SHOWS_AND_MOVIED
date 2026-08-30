"""
Global Sidebar Filters Component for Netflix Analytics Dashboard.
"""

from typing import Dict, Any, Tuple
import streamlit as st

POPULAR_COUNTRIES = [
    "All", "United States", "India", "United Kingdom", "Canada", "France",
    "Japan", "Spain", "South Korea", "Germany", "Mexico", "Australia"
]

POPULAR_GENRES = [
    "All", "International Movies", "Dramas", "Comedies", "International TV Shows",
    "Documentaries", "Action & Adventure", "TV Dramas", "Independent Movies",
    "Children & Family Movies", "TV Comedies", "Thrillers", "Romantic Movies"
]

POPULAR_RATINGS = [
    "All", "TV-MA", "TV-14", "TV-PG", "R", "PG-13", "TV-Y", "TV-Y7", "PG", "TV-G", "NR", "G"
]

AGE_GROUPS = [
    "All", "Adults (18+)", "Teens (13-17)", "Older Kids (7-12)", "Little Kids (0-6)", "Unrated"
]


def init_filter_state():
    """Ensure session state default variables exist for filtering."""
    if "f_content_type" not in st.session_state:
        st.session_state.f_content_type = "All"
    if "f_year_range" not in st.session_state:
        st.session_state.f_year_range = (1940, 2021)
    if "f_country" not in st.session_state:
        st.session_state.f_country = "All"
    if "f_genre" not in st.session_state:
        st.session_state.f_genre = "All"
    if "f_rating" not in st.session_state:
        st.session_state.f_rating = "All"
    if "f_age_group" not in st.session_state:
        st.session_state.f_age_group = "All"


def reset_filters():
    """Reset all filter states to defaults."""
    st.session_state.f_content_type = "All"
    st.session_state.f_year_range = (1940, 2021)
    st.session_state.f_country = "All"
    st.session_state.f_genre = "All"
    st.session_state.f_rating = "All"
    st.session_state.f_age_group = "All"


def render_sidebar_filters() -> Dict[str, Any]:
    """
    Render global filtering controls in the Streamlit sidebar.
    Returns standard filter dictionary suitable for ApiClient queries.
    """
    init_filter_state()

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
                <span style="color: #E50914; font-size: 1.8rem; font-weight: 900; letter-spacing: 2px;">NETFLIX</span>
                <br><span style="color: #888; font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase;">Live Analytics Platform</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### Catalog Filters")

        # 1. Content Type
        content_type = st.selectbox(
            "Content Type",
            options=["All", "Movie", "TV Show"],
            index=["All", "Movie", "TV Show"].index(st.session_state.f_content_type),
            key="f_content_type"
        )

        # 2. Release Year Range
        year_range = st.slider(
            "Release Year Range",
            min_value=1925,
            max_value=2021,
            value=st.session_state.f_year_range,
            key="f_year_range"
        )

        # 3. Country
        country = st.selectbox(
            "Country",
            options=POPULAR_COUNTRIES,
            index=POPULAR_COUNTRIES.index(st.session_state.f_country) if st.session_state.f_country in POPULAR_COUNTRIES else 0,
            key="f_country"
        )

        # 4. Genre
        genre = st.selectbox(
            "Genre Category",
            options=POPULAR_GENRES,
            index=POPULAR_GENRES.index(st.session_state.f_genre) if st.session_state.f_genre in POPULAR_GENRES else 0,
            key="f_genre"
        )

        # 5. Rating
        rating = st.selectbox(
            "Maturity Rating",
            options=POPULAR_RATINGS,
            index=POPULAR_RATINGS.index(st.session_state.f_rating) if st.session_state.f_rating in POPULAR_RATINGS else 0,
            key="f_rating"
        )

        # 6. Age Group
        age_group = st.selectbox(
            "Audience Demographic",
            options=AGE_GROUPS,
            index=AGE_GROUPS.index(st.session_state.f_age_group) if st.session_state.f_age_group in AGE_GROUPS else 0,
            key="f_age_group"
        )

        # Reset button
        st.button("Reset Filters", on_click=reset_filters, use_container_width=True)

    # Build active query dictionary
    filters: Dict[str, Any] = {}
    if content_type != "All":
        filters["content_type"] = content_type
    if year_range[0] > 1925:
        filters["release_year_min"] = year_range[0]
    if year_range[1] < 2021:
        filters["release_year_max"] = year_range[1]
    if country != "All":
        filters["country"] = country
    if genre != "All":
        filters["genre"] = genre
    if rating != "All":
        filters["rating"] = rating
    if age_group != "All":
        filters["age_group"] = age_group

    return filters


def render_active_filters_banner(filters: Dict[str, Any]):
    """Display active filters in a clean badge row."""
    if not filters:
        st.markdown(
            '<div style="color: #666; font-size: 0.85rem; margin-bottom: 1.2rem;">Showing full catalog (no active filters)</div>',
            unsafe_allow_html=True
        )
        return

    badges = []
    for k, v in filters.items():
        label = k.replace("_", " ").title()
        badges.append(f'<span style="background:#262626; border:1px solid #444; border-radius:4px; padding:2px 8px; margin-right:6px; font-size:0.8rem; color:#fff;"><strong>{label}:</strong> {v}</span>')

    st.markdown(
        f'<div style="margin-bottom: 1.2rem; display:flex; flex-wrap:wrap; align-items:center;"><span style="color:#aaa; font-size:0.85rem; margin-right:8px;">Active Filters:</span> {" ".join(badges)}</div>',
        unsafe_allow_html=True
    )
