"""
Dashboard components package.
"""

from dashboard.components.api_client import ApiClient
from dashboard.components.styling import (
    apply_netflix_theme,
    render_kpi_card,
    render_insight_card,
    render_section_header,
    NETFLIX_RED,
    NETFLIX_DARK
)
from dashboard.components.filters import render_sidebar_filters, render_active_filters_banner
from dashboard.components.charts import (
    plot_donut_chart,
    plot_horizontal_bar,
    plot_vertical_bar,
    plot_line_chart,
    plot_comparative_bars,
    plot_world_map
)
from dashboard.components.metrics import render_overview_kpi_row, render_freshness_banner

__all__ = [
    "ApiClient",
    "apply_netflix_theme",
    "render_kpi_card",
    "render_insight_card",
    "render_section_header",
    "render_sidebar_filters",
    "render_active_filters_banner",
    "plot_donut_chart",
    "plot_horizontal_bar",
    "plot_vertical_bar",
    "plot_line_chart",
    "plot_comparative_bars",
    "plot_world_map",
    "render_overview_kpi_row",
    "render_freshness_banner",
    "NETFLIX_RED",
    "NETFLIX_DARK",
]
