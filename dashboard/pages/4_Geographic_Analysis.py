"""
Page 4: Geographic Footprint & International Co-Productions Dashboard.
"""

import streamlit as st

st.set_page_config(page_title="Geographic Footprint | Netflix Analytics", page_icon="🌍", layout="wide")

from dashboard.components import (
    ApiClient,
    apply_netflix_theme,
    render_sidebar_filters,
    render_active_filters_banner,
    render_section_header,
    plot_horizontal_bar,
    plot_world_map
)

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">🌍 Geographic Production Footprint</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Analyze regional production hubs and international multi-country collaborations.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()
with st.spinner("Fetching Geographic Data from API..."):
    geo_resp = client.get_geographic_analysis(filters=filters)

if not geo_resp["success"]:
    st.error(f"⚠️ **API Error**: {geo_resp['error']}")
    st.stop()

geo = geo_resp["data"]
top_all = geo.get("top_countries_all_credits", {})
top_primary = geo.get("top_primary_countries", {})
co_prod_pct = geo.get("co_production_percentage", 0.0)
single_pct = geo.get("single_country_percentage", 0.0)
co_prod_count = geo.get("co_production_count", 0)
total_countries = geo.get("total_countries_represented", 0)

# 1. Global Interactive World Map
render_section_header("Interactive Global Production Map")
if top_all.get("labels"):
    st.plotly_chart(
        plot_world_map(top_all["labels"], top_all["values"], title="Global Production Volume by Country"),
        use_container_width=True
    )

# 2. Producing Country Rankings
render_section_header("Leading Content Producing Hubs")
col1, col2 = st.columns(2)

with col1:
    if top_all.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(
                top_all["labels"][:12],
                top_all["values"][:12],
                title="Top 12 Producing Countries (All Production Credits)",
                color="#E50914",
                height=450
            ),
            use_container_width=True
        )

with col2:
    if top_primary.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(
                top_primary["labels"][:12],
                top_primary["values"][:12],
                title="Top 12 Primary Producing Territories",
                color="#B81D24",
                height=450
            ),
            use_container_width=True
        )

# 3. International Co-Productions Summary
render_section_header("International Co-Production Dynamics")
c_stat1, c_stat2, c_stat3 = st.columns(3)

with c_stat1:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Countries Represented</div>
            <div class="netflix-kpi-value">{total_countries}</div>
            <div class="netflix-kpi-subtext">Distinct sovereign territories</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c_stat2:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Co-Production Rate</div>
            <div class="netflix-kpi-value">{co_prod_pct}%</div>
            <div class="netflix-kpi-subtext">{co_prod_count:,} multi-country titles</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c_stat3:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Single-Country Titles</div>
            <div class="netflix-kpi-value">{single_pct}%</div>
            <div class="netflix-kpi-subtext">Domestic sole-territory releases</div>
        </div>
        """,
        unsafe_allow_html=True
    )
