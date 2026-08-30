"""
Netflix-Themed Design Tokens and Global CSS Styling for Streamlit Dashboard.
"""

import streamlit as st

# Netflix Design Tokens
NETFLIX_RED = "#E50914"
NETFLIX_DARK = "#141414"
CARD_BG = "#1F1F1F"
CARD_BORDER = "#2E2E2E"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#AAAAAA"
GREEN_ACCENT = "#46D369"
GOLD_ACCENT = "#E5A914"


def apply_netflix_theme():
    """Inject global CSS rules to apply custom Netflix dark styling to Streamlit."""
    custom_css = f"""
    <style>
        /* Base page and font setup */
        @import url('https://fonts.googleapis.com/css2?family=Netflix+Sans:wght@400;500;700&family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}

        .stApp {{
            background-color: {NETFLIX_DARK};
            color: {TEXT_WHITE};
        }}

        /* Header Bar Styling */
        header[data-testid="stHeader"] {{
            background-color: rgba(20, 20, 20, 0.95);
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: #121212 !important;
            border-right: 1px solid {CARD_BORDER};
        }}

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {TEXT_WHITE} !important;
        }}

        /* Netflix Header Brand Banner */
        .netflix-brand-title {{
            color: {NETFLIX_RED};
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
        }}

        .netflix-brand-subtitle {{
            color: {TEXT_MUTED};
            font-size: 1.0rem;
            margin-bottom: 1.8rem;
        }}

        /* KPI / Metric Cards */
        .netflix-kpi-card {{
            background: linear-gradient(145deg, {CARD_BG} 0%, #262626 100%);
            border: 1px solid {CARD_BORDER};
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 1rem;
        }}

        .netflix-kpi-card:hover {{
            transform: translateY(-2px);
            border-color: {NETFLIX_RED};
            box-shadow: 0 6px 16px rgba(229, 9, 20, 0.15);
        }}

        .netflix-kpi-label {{
            color: {TEXT_MUTED};
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 0.3rem;
        }}

        .netflix-kpi-value {{
            color: {TEXT_WHITE};
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1.1;
        }}

        .netflix-kpi-subtext {{
            color: {GREEN_ACCENT};
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 0.4rem;
        }}

        /* Section Headings */
        .netflix-section-title {{
            color: {TEXT_WHITE};
            font-size: 1.4rem;
            font-weight: 700;
            border-left: 4px solid {NETFLIX_RED};
            padding-left: 0.8rem;
            margin-top: 1.8rem;
            margin-bottom: 1.2rem;
        }}

        /* Insight Cards */
        .netflix-insight-card {{
            background-color: {CARD_BG};
            border-left: 4px solid {NETFLIX_RED};
            border-radius: 4px 8px 8px 4px;
            padding: 1.1rem 1.4rem;
            margin-bottom: 0.9rem;
            border-top: 1px solid {CARD_BORDER};
            border-right: 1px solid {CARD_BORDER};
            border-bottom: 1px solid {CARD_BORDER};
        }}

        .netflix-insight-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.4rem;
        }}

        .netflix-insight-title {{
            color: {TEXT_WHITE};
            font-size: 1.05rem;
            font-weight: 700;
        }}

        .netflix-insight-badge {{
            background-color: rgba(229, 9, 20, 0.2);
            color: {NETFLIX_RED};
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.6rem;
            text-transform: uppercase;
        }}

        .netflix-insight-desc {{
            color: #CCCCCC;
            font-size: 0.92rem;
            line-height: 1.45;
        }}

        /* Primary Action Buttons */
        div.stButton > button:first-child {{
            background-color: {NETFLIX_RED};
            color: {TEXT_WHITE};
            border: none;
            border-radius: 4px;
            font-weight: 600;
            padding: 0.5rem 1.2rem;
            transition: background-color 0.2s ease, transform 0.1s ease;
        }}

        div.stButton > button:first-child:hover {{
            background-color: #F40612;
            color: {TEXT_WHITE};
            transform: scale(1.02);
        }}

        /* Status Badge Indicators */
        .status-badge-healthy {{
            background-color: rgba(70, 211, 105, 0.15);
            color: {GREEN_ACCENT};
            border: 1px solid {GREEN_ACCENT};
            border-radius: 20px;
            padding: 0.3rem 0.8rem;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }}

        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 1.5rem;
            border-bottom: 1px solid {CARD_BORDER};
        }}

        .stTabs [data-baseweb="tab"] {{
            padding: 0.8rem 0.5rem;
            color: {TEXT_MUTED};
            font-weight: 600;
        }}

        .stTabs [aria-selected="true"] {{
            color: {NETFLIX_RED} !important;
            border-bottom: 2px solid {NETFLIX_RED} !important;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, subtext: str = ""):
    """Render a styled Netflix KPI card."""
    subtext_html = f'<div class="netflix-kpi-subtext">{subtext}</div>' if subtext else ''
    html = f"""
    <div class="netflix-kpi-card">
        <div class="netflix-kpi-label">{label}</div>
        <div class="netflix-kpi-value">{value}</div>
        {subtext_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_insight_card(title: str, description: str, category: str, stat: str = ""):
    """Render a styled Netflix insight observation card."""
    badge_text = stat if stat else category.replace("_", " ")
    html = f"""
    <div class="netflix-insight-card">
        <div class="netflix-insight-header">
            <span class="netflix-insight-title">{title}</span>
            <span class="netflix-insight-badge">{badge_text}</span>
        </div>
        <div class="netflix-insight-desc">{description}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_section_header(title: str):
    """Render a section header with Netflix red bar accent."""
    st.markdown(f'<div class="netflix-section-title">{title}</div>', unsafe_allow_html=True)
