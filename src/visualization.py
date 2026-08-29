"""
Data Visualization Module for Netflix Movies and TV Shows Data Analysis.

Generates 12 publication-ready, beautifully styled charts using Matplotlib and Seaborn
with a signature Netflix dark-mode aesthetic (Netflix Crimson #E50914, Dark Charcoal #141414,
Crisp White #FFFFFF, and Muted Platinum #B3B3B3).
"""

import os
import sys

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

from src.data_cleaning import get_exploded_series, get_movies_df, get_tvshows_df
from src.exploratory_analysis import (
    analyze_content_type,
    analyze_countries,
    analyze_genres,
    analyze_temporal_trends,
    analyze_ratings_and_demographics,
    analyze_directors,
    analyze_cast,
    analyze_movie_durations,
    analyze_tv_shows,
    analyze_comparative
)

# -----------------------------------------------------------------------------
# Global Aesthetic Styling (Netflix Signature Theme)
# -----------------------------------------------------------------------------
NETFLIX_RED = "#E50914"
NETFLIX_DARK_RED = "#B81D24"
DARK_BG = "#141414"
CARD_BG = "#1F1F1F"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#A3A3A3"
ACCENT_GREY = "#333333"
ACCENT_GOLD = "#F5A623"
ACCENT_BLUE = "#0080FF"


def apply_netflix_theme():
    """Configure global Matplotlib and Seaborn aesthetic parameters."""
    sns.set_theme(style="dark", font_scale=1.05)
    plt.rcParams["figure.facecolor"] = DARK_BG
    plt.rcParams["axes.facecolor"] = CARD_BG
    plt.rcParams["axes.edgecolor"] = ACCENT_GREY
    plt.rcParams["axes.labelcolor"] = TEXT_WHITE
    plt.rcParams["xtick.color"] = TEXT_WHITE
    plt.rcParams["ytick.color"] = TEXT_WHITE
    plt.rcParams["text.color"] = TEXT_WHITE
    plt.rcParams["grid.color"] = "#2B2B2B"
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.6
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"]


def save_chart(fig, filename: str, output_dir: str = "visualizations"):
    """Save figure with high DPI and tight layout."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    fig.savefig(file_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"  [SAVED] {filename}")


# -----------------------------------------------------------------------------
# Chart 01: Movies vs TV Shows Distribution (Donut & Count Plot)
# -----------------------------------------------------------------------------
def plot_01_movies_vs_tvshows(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 1: Distribution and ratio of Movies vs TV Shows."""
    apply_netflix_theme()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.1, 1]})
    
    counts = df["type"].value_counts()
    colors = [NETFLIX_RED, "#6B7280"]
    
    # 1. Bar Chart
    bars = ax1.bar(counts.index, counts.values, color=colors, width=0.55, edgecolor="#000000", linewidth=1.2)
    ax1.set_title("Catalog Count: Movies vs TV Shows", fontsize=14, fontweight="bold", pad=15)
    ax1.set_ylabel("Number of Titles", fontsize=12, labelpad=10)
    ax1.set_ylim(0, max(counts.values) * 1.15)
    ax1.grid(axis="y", alpha=0.4)
    
    # Bar annotations
    for bar in bars:
        h = bar.get_height()
        pct = (h / len(df)) * 100
        ax1.annotate(f"{h:,}\n({pct:.1f}%)",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 6), textcoords="offset points",
                     ha="center", va="bottom", fontsize=11, fontweight="bold", color=TEXT_WHITE)
    
    # 2. Donut Chart
    wedges, texts, autotexts = ax2.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops={"color": TEXT_WHITE, "fontsize": 12, "fontweight": "bold"},
        wedgeprops={"width": 0.42, "edgecolor": DARK_BG, "linewidth": 2}
    )
    for autotext in autotexts:
        autotext.set_fontsize(13)
        autotext.set_fontweight("bold")
        
    ax2.set_title("Proportion of Catalog (%)", fontsize=14, fontweight="bold", pad=15)
    
    fig.suptitle("1. Netflix Content Type Distribution", fontsize=17, fontweight="bold", color=TEXT_WHITE, y=1.02)
    save_chart(fig, "01_movies_vs_tvshows.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 02: Top 10 Countries Producing Content
# -----------------------------------------------------------------------------
def plot_02_top10_countries(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 2: Top 10 content-producing countries (all production credits)."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(12, 7))
    
    country_series = get_exploded_series(df, "country")
    top10 = country_series.value_counts().head(10).sort_values(ascending=True)
    
    # Palette with US highlighted in primary Netflix Red
    colors = [NETFLIX_DARK_RED if c != "United States" else NETFLIX_RED for c in top10.index]
    
    bars = ax.barh(top10.index, top10.values, color=colors, height=0.65, edgecolor="#000000", linewidth=0.8)
    ax.set_title("2. Top 10 Countries Producing Netflix Content (All Production Credits)", 
                 fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Titles Produced / Co-Produced", fontsize=12, labelpad=10)
    ax.set_xlim(0, max(top10.values) * 1.15)
    ax.grid(axis="x", alpha=0.4)
    
    for bar in bars:
        w = bar.get_width()
        pct = (w / len(df)) * 100
        ax.annotate(f" {w:,} ({pct:.1f}%)",
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=10.5, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "02_top10_countries.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 03: Top 10 Genres / Categories
# -----------------------------------------------------------------------------
def plot_03_top10_genres(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 3: Top 10 most common genres/categories."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(13, 7))
    
    genres = get_exploded_series(df, "listed_in")
    top10 = genres.value_counts().head(10).sort_values(ascending=True)
    
    bars = ax.barh(top10.index, top10.values, color=NETFLIX_RED, height=0.65, edgecolor="#000000", linewidth=0.8)
    ax.set_title("3. Top 10 Genres / Content Categories on Netflix", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Titles Associated", fontsize=12, labelpad=10)
    ax.set_xlim(0, max(top10.values) * 1.15)
    ax.grid(axis="x", alpha=0.4)
    
    for bar in bars:
        w = bar.get_width()
        pct = (w / len(df)) * 100
        ax.annotate(f" {w:,} titles ({pct:.1f}%)",
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=10, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "03_top10_genres.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 04: Content Growth Over the Years (Catalog Additions)
# -----------------------------------------------------------------------------
def plot_04_content_growth(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 4: Content additions trajectory over time."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(12, 6.5))
    
    yearly = df["year_added"].dropna().astype(int).value_counts().sort_index()
    # Filter 2008+
    yearly = yearly[yearly.index >= 2008]
    
    ax.plot(yearly.index, yearly.values, color=NETFLIX_RED, marker="o", markersize=8, 
            linewidth=3, label="Annual Additions", zorder=4)
    ax.fill_between(yearly.index, yearly.values, color=NETFLIX_RED, alpha=0.25, zorder=3)
    
    ax.set_title("4. Netflix Content Addition Growth Trajectory (2008 – 2019)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Year Added to Netflix", fontsize=12, labelpad=10)
    ax.set_ylabel("Total Titles Added", fontsize=12, labelpad=10)
    ax.set_xticks(yearly.index)
    ax.set_xticklabels(yearly.index, rotation=35)
    ax.grid(True, alpha=0.4)
    ax.set_ylim(0, max(yearly.values) * 1.15)
    
    for x, y in zip(yearly.index, yearly.values):
        ax.annotate(f"{y:,}", xy=(x, y), xytext=(0, 9), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "04_content_growth_over_years.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 05: Content Added by Month (Seasonality)
# -----------------------------------------------------------------------------
def plot_05_monthly_additions(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 5: Monthly seasonality in content additions."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    
    months_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    monthly = df["month_name_added"].dropna().value_counts().reindex(months_order)
    
    # Highlight top months with brighter red
    top_month = monthly.idxmax()
    colors = [NETFLIX_RED if m == top_month else "#8E1616" for m in monthly.index]
    
    ax.set_xticks(range(len(monthly.index)))
    bars = ax.bar(range(len(monthly.index)), monthly.values, color=colors, width=0.6, edgecolor="#000000", linewidth=0.8)
    ax.set_title("5. Netflix Content Ingestion Seasonality (Additions by Month)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Calendar Month", fontsize=12, labelpad=10)
    ax.set_ylabel("Titles Added", fontsize=12, labelpad=10)
    ax.set_xticklabels(monthly.index, rotation=30)
    ax.set_ylim(0, max(monthly.values) * 1.18)
    ax.grid(axis="y", alpha=0.4)
    
    for bar in bars:
        h = bar.get_height()
        pct = (h / monthly.sum()) * 100
        ax.annotate(f"{int(h):,}\n({pct:.1f}%)", xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "05_monthly_content_additions.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 06: Rating Distribution (Segmented by Movies and TV Shows)
# -----------------------------------------------------------------------------
def plot_06_rating_distribution(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 6: Age rating distribution segmented by Movies and TV Shows."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Exclude minor or missing ratings for clean visual
    top_ratings = df["rating"].value_counts().head(10).index
    subset = df[df["rating"].isin(top_ratings)]
    
    ct = pd.crosstab(subset["rating"], subset["type"]).loc[top_ratings]
    
    x = np.arange(len(ct.index))
    width = 0.38
    
    bars1 = ax.bar(x - width/2, ct["Movie"], width=width, label="Movie", color=NETFLIX_RED, edgecolor="#000000")
    bars2 = ax.bar(x + width/2, ct["TV Show"], width=width, label="TV Show", color="#4B5563", edgecolor="#000000")
    
    ax.set_title("6. Content Rating Distribution: Movies vs TV Shows", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Age Rating / Maturity Certification", fontsize=12, labelpad=10)
    ax.set_ylabel("Number of Titles", fontsize=12, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(ct.index)
    ax.legend(frameon=True, facecolor=CARD_BG, edgecolor=ACCENT_GREY)
    ax.grid(axis="y", alpha=0.4)
    ax.set_ylim(0, max(ct.values.flatten()) * 1.15)
    
    for bar in list(bars1) + list(bars2):
        h = bar.get_height()
        if h > 20:
            ax.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=TEXT_WHITE)
                        
    save_chart(fig, "06_rating_distribution.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 07: Top 10 Directors
# -----------------------------------------------------------------------------
def plot_07_top_directors(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 7: Directors with highest number of titles."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(12, 7))
    
    directors = get_exploded_series(df, "director")
    top10 = directors.value_counts().head(10).sort_values(ascending=True)
    
    bars = ax.barh(top10.index, top10.values, color=NETFLIX_RED, height=0.65, edgecolor="#000000")
    ax.set_title("7. Top 10 Directors by Number of Titles on Netflix", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Total Titles Directed", fontsize=12, labelpad=10)
    ax.set_xlim(0, max(top10.values) * 1.2)
    ax.grid(axis="x", alpha=0.4)
    
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f" {int(w)} titles", xy=(w, bar.get_y() + bar.get_height()/2),
                    xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=10.5, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "07_top_directors.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 08: Top 10 Actors
# -----------------------------------------------------------------------------
def plot_08_top_actors(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 8: Most frequently cast actors globally."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(12, 7))
    
    cast_series = get_exploded_series(df, "cast")
    top10 = cast_series.value_counts().head(10).sort_values(ascending=True)
    
    bars = ax.barh(top10.index, top10.values, color=NETFLIX_RED, height=0.65, edgecolor="#000000")
    ax.set_title("8. Top 10 Most Frequently Appearing Actors / Actresses on Netflix", 
                 fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Title Appearances", fontsize=12, labelpad=10)
    ax.set_xlim(0, max(top10.values) * 1.2)
    ax.grid(axis="x", alpha=0.4)
    
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f" {int(w)} titles", xy=(w, bar.get_y() + bar.get_height()/2),
                    xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=10.5, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "08_top_actors.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 09: Movie Duration Histogram & KDE
# -----------------------------------------------------------------------------
def plot_09_movie_duration(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 9: Distribution of movie runtimes with statistical markers."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    
    movies_df = get_movies_df(df)
    durations = movies_df["duration_min"].dropna()
    
    mean_val = durations.mean()
    median_val = durations.median()
    
    sns.histplot(durations, bins=40, kde=True, color=NETFLIX_RED, ax=ax, 
                 edgecolor="#141414", line_kws={"linewidth": 2.5, "color": "#FFFFFF"})
    
    # Mark Mean and Median
    ax.axvline(mean_val, color=ACCENT_GOLD, linestyle="--", linewidth=2, label=f"Mean: {mean_val:.1f} min")
    ax.axvline(median_val, color="#00E5FF", linestyle=":", linewidth=2, label=f"Median: {median_val:.1f} min")
    
    ax.set_title("9. Netflix Movie Duration Distribution (in Minutes)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Duration (Minutes)", fontsize=12, labelpad=10)
    ax.set_ylabel("Number of Movies", fontsize=12, labelpad=10)
    ax.set_xlim(0, 250)
    ax.legend(frameon=True, facecolor=CARD_BG, edgecolor=ACCENT_GREY, fontsize=11)
    ax.grid(True, alpha=0.4)
    
    save_chart(fig, "09_movie_duration_distribution.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 10: TV Show Seasons Distribution
# -----------------------------------------------------------------------------
def plot_10_tvshow_seasons(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 10: Distribution of TV show season lengths."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(12, 6.5))
    
    tv_df = get_tvshows_df(df)
    seasons = tv_df["seasons"].dropna().value_counts().sort_index()
    # Focus on seasons 1 through 10
    seasons_subset = seasons[seasons.index <= 10]
    
    bars = ax.bar(seasons_subset.index, seasons_subset.values, color=NETFLIX_RED, width=0.6, edgecolor="#000000")
    ax.set_title("10. TV Shows Season Count Distribution (Seasons 1 to 10)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Seasons", fontsize=12, labelpad=10)
    ax.set_ylabel("Number of TV Shows", fontsize=12, labelpad=10)
    ax.set_xticks(seasons_subset.index)
    ax.set_ylim(0, max(seasons_subset.values) * 1.15)
    ax.grid(axis="y", alpha=0.4)
    
    for bar in bars:
        h = bar.get_height()
        pct = (h / len(tv_df)) * 100
        ax.annotate(f"{int(h):,}\n({pct:.1f}%)", xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=TEXT_WHITE)
                    
    save_chart(fig, "10_tvshow_seasons_distribution.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 11: Heatmap - Top Genres vs Age Rating Demographics
# -----------------------------------------------------------------------------
def plot_11_genre_rating_heatmap(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 11: Cross-tabulation heatmap of top genres across target age demographics."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(13, 8))
    
    # Explode listed_in and associate with age_group
    temp_df = df[["age_group", "listed_in"]].copy()
    temp_df["genre"] = temp_df["listed_in"].str.split(",")
    temp_exploded = temp_df.explode("genre").reset_index(drop=True)
    temp_exploded["genre"] = temp_exploded["genre"].str.strip()
    
    top_genres = temp_exploded["genre"].value_counts().head(10).index
    filtered = temp_exploded[temp_exploded["genre"].isin(top_genres)].reset_index(drop=True)
    
    ct = pd.crosstab(filtered["genre"], filtered["age_group"])
    # Sort columns logically
    col_order = ["Adults (18+)", "Teens (13-17)", "Older Kids (7-12)", "Little Kids (0-6)", "Unrated"]
    ct = ct[[c for c in col_order if c in ct.columns]]
    ct = ct.loc[top_genres]
    
    sns.heatmap(ct, annot=True, fmt="d", cmap="Reds", cbar=True, ax=ax,
                linewidths=1, linecolor=DARK_BG, annot_kws={"fontsize": 11, "fontweight": "bold"})
    
    ax.set_title("11. Heatmap: Top 10 Genres Across Audience Age Groups", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Target Audience Age Group", fontsize=12, labelpad=10)
    ax.set_ylabel("Content Genre", fontsize=12, labelpad=10)
    
    save_chart(fig, "11_genre_rating_heatmap.png", output_dir)


# -----------------------------------------------------------------------------
# Chart 12: Comparative Movies vs TV Shows Growth Over Time
# -----------------------------------------------------------------------------
def plot_12_movies_vs_tvshows_growth(df: pd.DataFrame, output_dir: str = "visualizations"):
    """Chart 12: Annual catalog additions trajectory comparing Movies vs TV Shows."""
    apply_netflix_theme()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    
    yearly_ct = pd.crosstab(df["year_added"], df["type"]).loc[2012:2019]
    
    ax.plot(yearly_ct.index, yearly_ct["Movie"], color=NETFLIX_RED, marker="o", 
            linewidth=3, markersize=8, label="Movies Added", zorder=4)
    ax.plot(yearly_ct.index, yearly_ct["TV Show"], color="#60A5FA", marker="s", 
            linewidth=3, markersize=8, label="TV Shows Added", zorder=4)
    
    ax.fill_between(yearly_ct.index, yearly_ct["Movie"], color=NETFLIX_RED, alpha=0.15)
    ax.fill_between(yearly_ct.index, yearly_ct["TV Show"], color="#60A5FA", alpha=0.15)
    
    ax.set_title("12. Comparative Annual Content Additions: Movies vs TV Shows (2012 – 2019)", 
                 fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Year Added to Netflix", fontsize=12, labelpad=10)
    ax.set_ylabel("Number of Titles Added", fontsize=12, labelpad=10)
    ax.set_xticks(yearly_ct.index)
    ax.legend(frameon=True, facecolor=CARD_BG, edgecolor=ACCENT_GREY, fontsize=11)
    ax.grid(True, alpha=0.4)
    ax.set_ylim(0, max(yearly_ct["Movie"].max(), yearly_ct["TV Show"].max()) * 1.18)
    
    for yr in yearly_ct.index:
        m_val = yearly_ct.loc[yr, "Movie"]
        tv_val = yearly_ct.loc[yr, "TV Show"]
        ax.annotate(f"{m_val}", xy=(yr, m_val), xytext=(0, 6), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, fontweight="bold", color=NETFLIX_RED)
        ax.annotate(f"{tv_val}", xy=(yr, tv_val), xytext=(0, 6), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, fontweight="bold", color="#60A5FA")
                    
    save_chart(fig, "12_movies_vs_tvshows_growth.png", output_dir)


# -----------------------------------------------------------------------------
# Master Generation Function
# -----------------------------------------------------------------------------
def generate_all_visualizations(data_path: str = "data/netflix_cleaned.csv", 
                                output_dir: str = "visualizations"):
    """
    Generate all 12 publication-quality visualizations and save to output_dir.
    """
    print("=" * 60)
    print("GENERATING PUBLICATION-QUALITY NETFLIX VISUALIZATIONS")
    print("=" * 60)
    
    if not os.path.exists(data_path):
        from src.data_cleaning import clean_netflix_pipeline
        clean_netflix_pipeline()
        
    df = pd.read_csv(data_path)
    
    plot_01_movies_vs_tvshows(df, output_dir)
    plot_02_top10_countries(df, output_dir)
    plot_03_top10_genres(df, output_dir)
    plot_04_content_growth(df, output_dir)
    plot_05_monthly_additions(df, output_dir)
    plot_06_rating_distribution(df, output_dir)
    plot_07_top_directors(df, output_dir)
    plot_08_top_actors(df, output_dir)
    plot_09_movie_duration(df, output_dir)
    plot_10_tvshow_seasons(df, output_dir)
    plot_11_genre_rating_heatmap(df, output_dir)
    plot_12_movies_vs_tvshows_growth(df, output_dir)
    
    print("=" * 60)
    print(f"[SUCCESS] All 12 charts successfully generated and saved to '{output_dir}/'.")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_visualizations()
