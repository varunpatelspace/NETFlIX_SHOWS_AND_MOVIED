"""
Page 1: Executive Overview Dashboard for Netflix Live Content Analytics.
"""

import streamlit as st

st.set_page_config(page_title="Executive Overview | Netflix Analytics", page_icon="📊", layout="wide")

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

apply_netflix_theme()
filters = render_sidebar_filters()

st.markdown('<div class="netflix-brand-title">📊 Executive Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">High-level catalog metrics, global footprint, and automated business observations.</div>', unsafe_allow_html=True)

render_active_filters_banner(filters)

client = ApiClient()
with st.spinner("Loading Executive Overview from API..."):
    summary_resp = client.get_dashboard_summary(filters=filters)
    status_resp = client.get_pipeline_status()

if not summary_resp["success"]:
    st.error(f"⚠️ **API Unavailable**: {summary_resp['error']}")
    st.info("Ensure the FastAPI backend is running via `uvicorn api.main:app --reload`.")
    st.stop()

data = summary_resp["data"]
overview = data.get("overview", {})
content = data.get("content", {})
temporal = data.get("temporal", {})
geographic = data.get("geographic", {})
insights = data.get("insights", [])
pipeline_status = status_resp.get("data", {}) if status_resp.get("success") else {}

# 1. KPI Cards
render_overview_kpi_row(overview)

# 2. Main Executive Visualizations
col1, col2 = st.columns(2)

with col1:
    type_data = content.get("content_type", {})
    if type_data.get("labels"):
        st.plotly_chart(
            plot_donut_chart(type_data["labels"], type_data["values"], title="Catalog Split: Movies vs TV Shows"),
            use_container_width=True
        )
    else:
        st.info("No content format records matching current filters.")

with col2:
    yearly = temporal.get("yearly_additions", {})
    if yearly.get("years"):
        st.plotly_chart(
            plot_line_chart(yearly["years"], yearly["counts"], title="Annual Content Additions Trajectory"),
            use_container_width=True
        )
    else:
        st.info("No addition trend records matching current filters.")

# 3. Top Genres & Top Territories
col3, col4 = st.columns(2)

with col3:
    genres = content.get("top_genres_overall", {})
    if genres.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(genres["labels"][:10], genres["values"][:10], title="Top 10 Global Content Categories"),
            use_container_width=True
        )

with col4:
    geo = geographic.get("top_countries_all_credits", {})
    if geo.get("labels"):
        st.plotly_chart(
            plot_horizontal_bar(geo["labels"][:10], geo["values"][:10], title="Top 10 Producing Territories", color="#991419"),
            use_container_width=True
        )

# 4. Insights
render_section_header("Evidence-Based Business Observations")
if insights:
    i_col1, i_col2 = st.columns(2)
    for idx, ins in enumerate(insights):
        target = i_col1 if idx % 2 == 0 else i_col2
        with target:
            render_insight_card(
                title=ins.get("title", ""),
                description=ins.get("description", ""),
                category=ins.get("category", ""),
                stat=ins.get("stat", "")
            )
else:
    st.info("No observations generated for current filter criteria.")

# 5. Freshness
render_freshness_banner(pipeline_status)
