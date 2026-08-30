"""
Reusable Interactive Plotly Charts styled with Netflix Dark Design Aesthetics.
"""

from typing import List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px

NETFLIX_RED = "#E50914"
NETFLIX_DARK = "#141414"
CARD_BG = "#1F1F1F"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#AAAAAA"
GRID_COLOR = "#2E2E2E"


def _apply_dark_layout(fig: go.Figure, title: str, height: int = 380) -> go.Figure:
    """Standardize dark mode layout across all charts."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "font": {"size": 16, "color": TEXT_WHITE, "family": "Inter, sans-serif"},
            "x": 0.02,
            "y": 0.95
        },
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font={"color": TEXT_WHITE, "family": "Inter, sans-serif"},
        margin={"l": 40, "r": 30, "t": 60, "b": 40},
        height=height,
        legend={"font": {"color": TEXT_WHITE}, "bgcolor": "rgba(0,0,0,0)"},
        hoverlabel={"bgcolor": "#2B2B2B", "font_size": 12, "font_family": "Inter"}
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        tickfont={"color": TEXT_MUTED}
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        tickfont={"color": TEXT_MUTED}
    )
    return fig


def plot_donut_chart(labels: List[str], values: List[int], title: str = "Content Split") -> go.Figure:
    """Create a sleek donut chart."""
    colors = [NETFLIX_RED, "#6B0A0F", "#B81D24", "#FF4F58"]
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors[:len(labels)], line=dict(color=CARD_BG, width=2)),
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        textfont=dict(color=TEXT_WHITE, size=13)
    )])
    return _apply_dark_layout(fig, title)


def plot_horizontal_bar(
    labels: List[str],
    values: List[int],
    title: str,
    color: str = NETFLIX_RED,
    height: int = 400
) -> go.Figure:
    """Create a clean horizontal bar chart."""
    # Reverse so top item is on top
    rev_labels = list(reversed(labels))
    rev_values = list(reversed(values))

    fig = go.Figure(data=[go.Bar(
        x=rev_values,
        y=rev_labels,
        orientation="h",
        marker=dict(color=color, cornerradius=4),
        text=[f"{v:,}" for v in rev_values],
        textposition="auto",
        textfont=dict(color=TEXT_WHITE)
    )])
    fig.update_xaxes(title="Count")
    return _apply_dark_layout(fig, title, height=height)


def plot_vertical_bar(
    labels: List[str],
    values: List[int],
    title: str,
    color: str = NETFLIX_RED,
    height: int = 380
) -> go.Figure:
    """Create a vertical bar chart."""
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker=dict(color=color, cornerradius=4),
        text=[f"{v:,}" for v in values],
        textposition="outside",
        textfont=dict(color=TEXT_WHITE)
    )])
    return _apply_dark_layout(fig, title, height=height)


def plot_line_chart(
    x: List[Any],
    y: List[Any],
    title: str,
    line_color: str = NETFLIX_RED,
    fill_area: bool = True
) -> go.Figure:
    """Create a trend line chart with optional subtle fill gradient."""
    fill = "tozeroy" if fill_area else "none"
    fig = go.Figure(data=[go.Scatter(
        x=x,
        y=y,
        mode="lines+markers",
        line=dict(color=line_color, width=3),
        marker=dict(size=6, color=line_color),
        fill=fill,
        fillcolor="rgba(229, 9, 20, 0.15)"
    )])
    return _apply_dark_layout(fig, title)


def plot_comparative_bars(
    categories: List[Any],
    series_a: List[int],
    series_b: List[int],
    name_a: str = "Movies",
    name_b: str = "TV Shows",
    title: str = "Comparative Additions"
) -> go.Figure:
    """Create a grouped bar chart comparing two series."""
    fig = go.Figure(data=[
        go.Bar(name=name_a, x=categories, y=series_a, marker=dict(color=NETFLIX_RED, cornerradius=3)),
        go.Bar(name=name_b, x=categories, y=series_b, marker=dict(color="#545454", cornerradius=3))
    ])
    fig.update_layout(barmode="group")
    return _apply_dark_layout(fig, title)


def plot_world_map(countries: List[str], counts: List[int], title: str = "Global Content Footprint") -> go.Figure:
    """Create an interactive choropleth world map."""
    fig = go.Figure(data=go.Choropleth(
        locations=countries,
        locationmode="country names",
        z=counts,
        colorscale=[
            [0, "#262626"],
            [0.1, "#541013"],
            [0.4, "#991419"],
            [0.8, "#D81F26"],
            [1.0, "#FF4047"]
        ],
        marker_line_color="#1F1F1F",
        colorbar_title="Titles",
        colorbar_tickfont=dict(color=TEXT_WHITE)
    ))
    fig.update_geos(
        showcoastlines=True,
        coastlinecolor=GRID_COLOR,
        showland=True,
        landcolor="#1A1A1A",
        showocean=True,
        oceancolor="#0E0E0E",
        showlakes=False,
        bgcolor=CARD_BG
    )
    return _apply_dark_layout(fig, title, height=450)
