"""
Page 7: Interactive Content Explorer & Catalog Browser.
"""

import math
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Content Explorer | Netflix Analytics", page_icon="🔍", layout="wide")

from dashboard.components import (
    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_section_header
)

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">🔍 Content Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Browse, search, and inspect catalog titles with server-side pagination and attribute detail.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()

# Search Bar & Pagination Controls
col_search, col_page_size = st.columns([3, 1])

with col_search:
    search_query = st.text_input("Search by Title, Director, or Cast keyword:", placeholder="e.g. Stranger Things, Leonardo DiCaprio, Scorsese...")

with col_page_size:
    page_size = st.selectbox("Titles per page", options=[15, 25, 50], index=0)

# Track current page in session state
if "catalog_page" not in st.session_state:
    st.session_state.catalog_page = 1

# Reset to page 1 if search query changes
if "last_search" not in st.session_state or st.session_state.last_search != search_query:
    st.session_state.catalog_page = 1
    st.session_state.last_search = search_query

offset = (st.session_state.catalog_page - 1) * page_size

with st.spinner("Fetching catalog page from API..."):
    resp = client.get_content(
        limit=page_size,
        offset=offset,
        search=search_query if search_query.strip() else None,
        filters=filters
    )

if not resp["success"]:
    st.error(f"⚠️ **API Error**: {resp['error']}")
    st.stop()

catalog_data = resp["data"]
total_matching = catalog_data.get("total", 0)
items = catalog_data.get("data", [])
total_pages = max(1, math.ceil(total_matching / page_size))

# Navigation Bar
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

with nav_col1:
    if st.button("⬅️ Previous Page", disabled=(st.session_state.catalog_page <= 1), use_container_width=True):
        st.session_state.catalog_page -= 1
        st.rerun()

with nav_col2:
    st.markdown(
        f'<div style="text-align:center; padding: 0.5rem; color:#aaa;">Page <strong>{st.session_state.catalog_page}</strong> of <strong>{total_pages}</strong> ({total_matching:,} matching titles)</div>',
        unsafe_allow_html=True
    )

with nav_col3:
    if st.button("Next Page ➡️", disabled=(st.session_state.catalog_page >= total_pages), use_container_width=True):
        st.session_state.catalog_page += 1
        st.rerun()

if not items:
    st.info("No catalog titles matched your filter or search criteria.")
else:
    # Build Display Table
    table_rows = []
    for it in items:
        table_rows.append({
            "Show ID": it.get("show_id"),
            "Title": it.get("title"),
            "Type": it.get("type"),
            "Year": it.get("release_year"),
            "Rating": it.get("rating"),
            "Duration": it.get("duration"),
            "Country": it.get("primary_country") or it.get("country"),
            "Genres": it.get("listed_in")
        })

    df_display = pd.DataFrame(table_rows)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Title Selection for Detail View
    render_section_header("Title Detail Inspection")
    title_options = {f"{it.get('title')} ({it.get('release_year')}) [{it.get('type')}]": it.get("show_id") for it in items}
    selected_label = st.selectbox("Select a title to inspect complete metadata:", options=list(title_options.keys()))

    if selected_label:
        selected_show_id = title_options[selected_label]
        with st.spinner("Fetching title details from API..."):
            detail_resp = client.get_content_detail(selected_show_id)

        if detail_resp["success"]:
            d = detail_resp["data"]
            # Render Styled Detail Card
            st.markdown(
                f"""
                <div style="background-color: #1F1F1F; border: 1px solid #E50914; border-radius: 8px; padding: 1.8rem; margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h2 style="color: #fff; margin: 0; font-size: 1.8rem;">{d.get('title')}</h2>
                        <span style="background: #E50914; color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;">{d.get('type')}</span>
                    </div>
                    <div style="color: #888; font-size: 0.95rem; margin-top: 0.3rem;">
                        {d.get('release_year')} | {d.get('rating')} | {d.get('duration')} | {d.get('age_group')}
                    </div>
                    <hr style="border-color: #333; margin: 1rem 0;">
                    <p style="color: #ddd; font-size: 1.05rem; line-height: 1.5;">{d.get('description')}</p>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.8rem; margin-top: 1.2rem; font-size: 0.9rem;">
                        <div><strong style="color:#aaa;">Director:</strong> <span style="color:#fff;">{d.get('director') or 'Not Listed'}</span></div>
                        <div><strong style="color:#aaa;">Country:</strong> <span style="color:#fff;">{d.get('country') or 'Unknown'}</span></div>
                        <div><strong style="color:#aaa;">Cast:</strong> <span style="color:#fff;">{d.get('cast') or 'Not Listed'}</span></div>
                        <div><strong style="color:#aaa;">Genres:</strong> <span style="color:#fff;">{d.get('listed_in')}</span></div>
                        <div><strong style="color:#aaa;">Date Added:</strong> <span style="color:#fff;">{d.get('date_added') or 'N/A'}</span></div>
                        <div><strong style="color:#aaa;">Licensing Lag:</strong> <span style="color:#46D369;">{d.get('release_to_add_lag')} years</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
