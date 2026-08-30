# Existing Project Analysis: Netflix Movies & Shows Data Analysis

**Document Version:** 1.0.0  
**Date:** August 2026  
**Author:** Senior Data Engineer & Platform Architect  
**Project:** Netflix Live Content Analytics Platform  

---

## 1. Executive Summary

This document provides a thorough audit and structural evaluation of the existing **Netflix Movies & Shows Data Analysis** project. The existing project is a static exploratory data analysis (EDA) and business intelligence system built with Python, Pandas, NumPy, Matplotlib, Seaborn, and Jupyter Notebook.

Per the architectural mandate, **no existing analysis functionality will be destroyed, replaced, or degraded**. Instead, the existing cleaning routines, feature engineering pipelines, and analytical calculations will serve as the analytical foundation for the upgraded **Netflix Live Content Analytics Platform**.

---

## 2. Current Project Architecture & File Inventory

### 2.1 File Tree
```
c:\Users\varun\Downloads\Netflix Shows and Movies\
├── data/
│   ├── netflix_titles.csv          # Raw Netflix dataset (5,840 lines / 5,837 data records)
│   └── netflix_cleaned.csv         # Cleaned, standardized dataset (5,834 records, 31 columns)
├── notebooks/
│   └── netflix_analysis.ipynb      # Interactive EDA Jupyter notebook
├── reports/
│   └── insights.md                 # Static business intelligence report
├── src/
│   ├── __init__.py                 # Package initialization
│   ├── data_cleaning.py            # End-to-end data cleaning & feature engineering module (421 lines)
│   ├── exploratory_analysis.py     # Modular analytical calculations (409 lines)
│   └── visualization.py            # Matplotlib/Seaborn Netflix dark-theme plotting suite (514 lines)
├── visualizations/                 # 12 high-resolution (300 DPI) static charts
│   ├── 01_movies_vs_tvshows.png
│   ├── 02_top10_countries.png
│   ├── 03_top10_genres.png
│   ├── 04_content_growth_over_years.png
│   ├── 05_monthly_content_additions.png
│   ├── 06_rating_distribution.png
│   ├── 07_top_directors.png
│   ├── 08_top_actors.png
│   ├── 09_movie_duration_distribution.png
│   ├── 10_tvshow_seasons_distribution.png
│   ├── 11_genre_rating_heatmap.png
│   └── 12_movies_vs_tvshows_growth.png
├── requirements.txt                # Static dependencies (pandas, numpy, matplotlib, seaborn, jupyter)
├── run_analysis.py                 # Master command-line orchestrator for batch execution
└── README.md                       # Project documentation & portfolio overview
```

### 2.2 Existing File Inventory & Descriptions
| File Path | Category | Purpose & Key Contents |
| :--- | :--- | :--- |
| `data/netflix_titles.csv` | Dataset | Raw input data containing 12 columns: `show_id`, `title`, `director`, `cast`, `country`, `date_added`, `release_year`, `rating`, `duration`, `listed_in`, `description`, `type`. |
| `data/netflix_cleaned.csv` | Dataset | Processed dataset created by `clean_netflix_pipeline()` containing 5,834 rows and 31 feature columns. |
| `src/data_cleaning.py` | Pipeline Logic | Implements 10 specialized functions for text trimming, deduplication, date parsing, duration parsing, rating categorization, missing value imputation, and feature engineering. |
| `src/exploratory_analysis.py`| Analytics Engine | Contains 10 statistical analysis routines computing distributions, aggregations, cross-tabulations, and rankings across all business dimensions. |
| `src/visualization.py` | Presentation | Defines the Netflix custom theme (`#E50914`, `#141414`, `#1F1F1F`) and exports 12 publication-grade figures. |
| `run_analysis.py` | Orchestration | CLI execution script invoking cleaning -> EDA -> chart generation in sequence. |
| `notebooks/netflix_analysis.ipynb` | Exploration | Step-by-step interactive workflow executing the `src` modules with embedded markdown summaries. |
| `reports/insights.md` | Business Intelligence | Static report detailing executive findings, catalog composition, geographic insights, and recommendations. |

---

## 3. Current Data Flow

The existing workflow operates as a strictly static, offline batch pipeline:

```
[Raw CSV File] (data/netflix_titles.csv)
       ↓
[load_dataset()] (Pandas read_csv)
       ↓
[inspect_raw_data()] (Missing values & duplicate check logged to console)
       ↓
[clean_text_formatting()] (Whitespace stripping & unicode sanitation)
       ↓
[handle_duplicates()] (Subset deduplication on title, type, release_year)
       ↓
[parse_dates_and_times()] (pd.to_datetime, derive year_added, month_added, lag)
       ↓
[parse_durations()] (Extract duration_min, seasons, movie_duration_tier)
       ↓
[categorize_ratings()] (Map ratings to 5 age_group tiers)
       ↓
[handle_missing_values()] (Impute Unknown Director, Cast, Country, Unavailable)
       ↓
[engineer_multi_value_features()] (Extract primary_country, counts, flags)
       ↓
[Cleaned CSV Output] (data/netflix_cleaned.csv)
       ├──→ [exploratory_analysis.py] → Console printouts & dictionary outputs
       ├──→ [visualization.py]        → 12 static PNG images in visualizations/
       └──→ [notebooks/]              → Static execution in Jupyter
```

---

## 4. Detailed Data Cleaning Pipeline Analysis

The current cleaning pipeline implemented in `src/data_cleaning.py` is well-structured and contains the following operations:

1. **Text Formatting (`clean_text_formatting`)**:
   - Strips leading and trailing whitespaces on all string columns.
   - Replaces literal string values `"nan"`, `"None"`, and `""` with actual `np.nan`.
   - Cleans unicode replacement characters (`\ufffd`).

2. **Deduplication (`handle_duplicates`)**:
   - Removes exact duplicate rows.
   - Prunes duplicate titles based on `subset=["title", "type", "release_year"]`, keeping the first occurrence.
   - Retains legitimate remakes (e.g., *Benji* 1974 vs *Benji* 2018).

3. **Temporal Processing (`parse_dates_and_times`)**:
   - Converts `date_added` using `pd.to_datetime(format="mixed", errors="coerce")`.
   - Derives `year_added` (Int64), `month_added` (Int64), `month_name_added` (str), and `day_added` (Int64).
   - Derives `release_to_add_lag` = `year_added - release_year`.

4. **Duration Parsing (`parse_durations`)**:
   - Extracts regex integer `(\d+)` from string `duration`.
   - Assigns `duration_min` for Movies; leaves `NaN` for TV Shows.
   - Assigns `seasons` (Int64) for TV Shows; leaves `NaN` for Movies.
   - Bins `duration_min` into 5 tiers: `< 60 min (Short)`, `60-90 min (Standard)`, `90-120 min (Feature)`, `120-150 min (Long)`, `> 150 min (Epic)`.

5. **Audience Demographics (`categorize_ratings`)**:
   - Maps 14 discrete MPAA/TV ratings into 5 standardized target audience demographics:
     - `Adults (18+)`: TV-MA, R, NC-17
     - `Teens (13-17)`: TV-14, PG-13
     - `Older Kids (7-12)`: TV-PG, PG
     - `Little Kids (0-6)`: TV-Y, TV-Y7, TV-Y7-FV, TV-G, G
     - `Unrated`: NR, UR, Unavailable

6. **Missing Value Imputation (`handle_missing_values`)**:
   - `director` (32.5% missing) -> Imputed with `"Unknown Director"`.
   - `cast` (9.5% missing) -> Imputed with `"Unknown Cast"`.
   - `country` (7.3% missing) -> Imputed with `"Unknown Country"`.
   - `rating` (0.17% missing) -> Imputed with `"Unavailable"`.
   - Adds explicit missingness indicator flags: `has_director_info`, `has_cast_info`, `has_country_info`, `has_date_added`.

7. **Multi-Value Feature Engineering (`engineer_multi_value_features`)**:
   - `primary_country`: First country listed in comma-separated string.
   - `country_count`: Number of countries producing the title.
   - `is_multi_country`: Boolean flag (`country_count > 1`).
   - `primary_genre`: First genre listed in comma-separated `listed_in`.
   - `genre_count`: Count of assigned genres.
   - `cast_count`: Total listed cast members.

---

## 5. Existing Analysis Modules & Output Schema

The existing exploratory modules in `src/exploratory_analysis.py` cover 10 core dimensions:

1. `analyze_content_type(df)`: Movie vs TV Show frequency and percentage distribution.
2. `analyze_countries(df, top_n=15)`: Unnested countries list, primary country counts, international co-production rate.
3. `analyze_genres(df, top_n=15)`: Global genre counts, movie genre breakdown, TV show genre breakdown, total unique genres.
4. `analyze_temporal_trends(df)`: Yearly additions, release year trajectory (1995+), monthly addition seasonality, licensing lag statistics (mean, median, % same-year).
5. `analyze_ratings_and_demographics(df)`: Rating frequency, rating by content type cross-tabulation, age group demographics breakdown.
6. `analyze_directors(df, top_n=15)`: Top directors across all titles, top movie directors, unique director count.
7. `analyze_cast(df, top_n=15)`: Top actors globally, top actors in India, top actors in United States, unique actor count.
8. `analyze_movie_durations(df)`: Descriptive statistics (count, mean, median, std, min, max, IQR), top 5 longest movies, top 5 shortest movies, duration tier distribution.
9. `analyze_tv_shows(df)`: Season count distribution, single-season share, 2-season share, 3+ seasons share, top 10 longest-running TV shows.
10. `analyze_comparative(df)`: Multi-dimensional cross-tabulations: Country vs Type, Rating vs Type, Year Added vs Type.

---

## 6. Existing Visualizations

The current visualization suite in `src/visualization.py` exports 12 static PNG files to `visualizations/`:

| Chart ID | File Name | Visual Type | Key Metrics / Insight |
| :--- | :--- | :--- | :--- |
| **01** | `01_movies_vs_tvshows.png` | Bar Chart + Donut Chart | 67.5% Movies (3,937) vs 32.5% TV Shows (1,897). |
| **02** | `02_top10_countries.png` | Horizontal Bar Chart | US (2,421 titles), India (752), UK (559). |
| **03** | `03_top10_genres.png` | Horizontal Bar Chart | International Movies, Dramas, Comedies. |
| **04** | `04_content_growth_over_years.png` | Line Plot + Area Fill | Exponential growth trajectory 2008–2019. |
| **05** | `05_monthly_content_additions.png`| Bar Chart | Seasonality: January, October, November, December peaks. |
| **06** | `06_rating_distribution.png` | Grouped Bar Chart | Ratings segmented by Movie and TV Show. |
| **07** | `07_top_directors.png` | Horizontal Bar Chart | Top prolific directors (e.g. Raúl Campos, Jan Suter). |
| **08** | `08_top_actors.png` | Horizontal Bar Chart | Top actors (e.g. Anupam Kher, Shah Rukh Khan). |
| **09** | `09_movie_duration_distribution.png`| Histogram + KDE | Median runtime: 97.0 min, IQR: 85–113 min. |
| **10** | `10_tvshow_seasons_distribution.png`| Bar Chart | Single-season shows (67.4%), 2-season (17.3%). |
| **11** | `11_genre_rating_heatmap.png`| Annotated Heatmap | Top 10 genres cross-tabulated with 5 age groups. |
| **12** | `12_movies_vs_tvshows_growth.png` | Dual Line Plot | Comparative addition trajectories (2012–2019). |

---

## 7. Reusable Components

The following components from the existing project will be directly reused without modification:

1. **Cleaning and Transformation Logic**:
   - `clean_text_formatting` -> Directly reusable in `pipeline/clean_data.py`.
   - `parse_dates_and_times` -> Directly reusable in `pipeline/transform_data.py`.
   - `parse_durations` -> Directly reusable in `pipeline/transform_data.py`.
   - `categorize_ratings` -> Directly reusable in `pipeline/transform_data.py`.
   - `handle_missing_values` -> Directly reusable in `pipeline/clean_data.py`.
   - `engineer_multi_value_features` -> Directly reusable in `pipeline/transform_data.py`.
   - `get_exploded_series`, `get_movies_df`, `get_tvshows_df` -> Reusable across ETL and Analytics.

2. **Analytical Logic**:
   - The aggregation, cross-tabulation, and statistical calculations from `analyze_content_type`, `analyze_countries`, `analyze_genres`, `analyze_temporal_trends`, `analyze_ratings_and_demographics`, `analyze_directors`, `analyze_cast`, `analyze_movie_durations`, `analyze_tv_shows`, and `analyze_comparative` will form the core of the `analytics/` service modules.

3. **Visual Identity**:
   - The Netflix color palette (`NETFLIX_RED = #E50914`, `DARK_BG = #141414`, `CARD_BG = #1F1F1F`, `TEXT_WHITE = #FFFFFF`, `ACCENT_GOLD = #F5A623`, `ACCENT_BLUE = #0080FF`) will be preserved in the Streamlit dashboard and API response metadata.

---

## 8. Limitations of the Current Static System & Required Improvements

| Dimension | Current State | Required Upgraded State |
| :--- | :--- | :--- |
| **Data Ingestion** | Hardcoded static CSV read from `data/netflix_titles.csv`. | Modular data source layer supporting CSV ingestion, batch simulation, API sources, and configurable connectors. |
| **Validation** | Ad-hoc terminal prints with no schema enforcement or rejection of corrupt rows. | Formal validation stage verifying column schemas, data types, null constraints, and invalid record filtering. |
| **Deduplication** | In-memory Pandas `drop_duplicates` on a single static file. | Stateful deduplication matching incoming records against database records using `show_id` as primary key and `(title, type, release_year)` fallback. |
| **Persistence** | Generates flat CSV (`data/netflix_cleaned.csv`). | Relational database (SQLite default, PostgreSQL compatible) with SQLAlchemy ORM and repository layer. |
| **Analytics Execution** | Notebook or CLI script coupled to file reading. | Decoupled analytics engine reading directly from database, providing structured Python dictionaries and DataFrames. |
| **Service Layer** | None. No network endpoints or machine-readable interface. | Production-grade FastAPI backend exposing RESTful JSON endpoints for all analytic dimensions. |
| **User Interface** | Static PNG files in a folder and static Jupyter notebook. | Real-time interactive Streamlit dashboard featuring live KPI cards, interactive filters (type, year, country, genre), and dynamic charts. |
| **Refresh Capability** | Manual terminal re-run of `run_analysis.py`. | Both manual ("Refresh Data" button in dashboard/API) and scheduled (APScheduler background job) pipeline triggers. |
| **Configuration** | Hardcoded relative file paths in scripts. | Centralized configuration via `config/settings.py` and `.env` environment variables. |
| **Observability** | `print()` statements scattered across modules. | Structured Python `logging` to file and console with rotation, severity levels, and execution metrics. |
| **Testing** | No automated tests. | Comprehensive `pytest` test suite covering validation, cleaning, deduplication, database queries, and API endpoints. |

---

## 9. Conclusion & Next Steps

The existing project has a solid data processing foundation. All domain-specific data cleaning rules, rating classifications, duration parsers, and statistical calculations are validated and functioning. 

The upgrade will wrap this analytical core in a production-grade data engineering architecture (modular sources, database repository, ETL pipeline, FastAPI backend, interactive Streamlit dashboard, and automated scheduling) while maintaining 100% backward compatibility.
