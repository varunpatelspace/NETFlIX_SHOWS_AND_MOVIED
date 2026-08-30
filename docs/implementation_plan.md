# Implementation Plan: Netflix Live Content Analytics Platform

**Document Version:** 1.0.0  
**Date:** August 2026  
**Status:** Under Review / Planning Mode  
**Author:** Senior Data Engineer, Data Analyst, Backend Developer & Dashboard Architect  

---

## 1. Introduction & Objectives

This document establishes the architecture, migration roadmap, and technical design for upgrading the existing static **Netflix Movies & Shows Data Analysis** project into an enterprise-grade **Netflix Live Content Analytics Platform**.

The upgraded platform transforms an offline batch EDA project into an automated, real-time analytics engine where:
1. Data is ingested dynamically from configurable data sources (CSV files, batch simulations, REST APIs).
2. Incoming batches undergo strict schema validation, type checking, and anomaly screening.
3. Records are cleaned and feature-engineered using the battle-tested rules from the existing project.
4. Deduplication eliminates redundant titles using `show_id` primary key tracking and fuzzy/subset fallback matching.
5. Cleaned data is persisted in a relational database with an ORM abstraction (SQLite for local zero-config execution, PostgreSQL-ready).
6. An analytics engine dynamically computes KPI metrics, geographic breakdowns, temporal trends, genre distributions, and cast/director rankings directly from database queries.
7. A FastAPI backend provides high-performance RESTful JSON endpoints.
8. A modern, dark-mode Streamlit dashboard visualizes KPIs, interactive charts, and business intelligence with filterable dimensions.
9. The platform supports both manual UI-driven refreshes and background scheduling (APScheduler) with configurable frequencies.

---

## 2. Current vs. Target Architecture

### 2.1 Current Static Architecture
```
[Raw CSV: data/netflix_titles.csv]
              ↓
  [src/data_cleaning.py]
              ↓
[Cleaned CSV: data/netflix_cleaned.csv]
      ↙                  ↘
[src/exploratory_analysis.py]   [src/visualization.py]
      ↓                                  ↓
[Console Output]                 [12 Static PNGs in visualizations/]
```
*Characteristics*: Static, single-run, file-coupled, no database, no API, no interactivity, no automation.

---

### 2.2 Target Automated Live Architecture
```
                                 ┌─────────────────────────┐
                                 │   Configurable Sources  │
                                 │ CSV / Delta / REST API  │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Data Fetching Layer   │
                                 │  (pipeline/fetch_data)  │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │    Raw Data Storage     │
                                 │      (data/raw/)        │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │     Data Validation     │
                                 │(pipeline/validate_data) │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │    Data Cleaning &      │
                                 │     Transformation      │
                                 │ (clean_data/transform)  │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │  Deduplication Engine   │
                                 │ (pipeline/deduplicate)  │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │    Database Storage     │
                                 │  (database/models.py)   │
                                 │ (netflix_content table) │
                                 └────────────┬────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
                       ▼                                             ▼
          ┌─────────────────────────┐                   ┌─────────────────────────┐
          │    Analytics Engine     │                   │   Background Scheduler  │
          │  (analytics/*.py)       │                   │ (scheduler/scheduler.py)│
          └────────────┬────────────┘                   └────────────┬────────────┘
                       │                                             │
                       ▼                                             │ Triggers Pipeline
          ┌─────────────────────────┐                                │ on Cron / Interval
          │     Backend REST API    │                                │
          │     (backend/main.py)   │                                │
          └────────────┬────────────┘                                │
                       │                                             │
                       ▼                                             │
          ┌─────────────────────────┐                                │
          │   Interactive Streamlit │ ◄──────────────────────────────┘
          │        Dashboard        │      (Auto-Refresh & Manual Button)
          └─────────────────────────┘
```

---

## 3. Migration & Preservation Strategy

To fulfill the mandate that **the existing data analysis remains intact, functional, and foundational**:
1. **Preserve Existing Files**:
   - `data/netflix_titles.csv` and `data/netflix_cleaned.csv` remain in `data/`.
   - `src/data_cleaning.py`, `src/exploratory_analysis.py`, and `src/visualization.py` remain untouched and operational.
   - `run_analysis.py` continues to execute the original batch flow without error.
   - `notebooks/netflix_analysis.ipynb` and `reports/insights.md` remain valid.
2. **Reuse Existing Logic**:
   - The modular routines in `src/data_cleaning.py` (`clean_text_formatting`, `parse_dates_and_times`, `parse_durations`, `categorize_ratings`, `handle_missing_values`, `engineer_multi_value_features`) will be imported or ported directly into `pipeline/clean_data.py` and `pipeline/transform_data.py`.
   - The analytical calculations in `src/exploratory_analysis.py` will be encapsulated in `analytics/` modules that query the database repository.
   - Visual styling rules (`NETFLIX_RED`, `DARK_BG`, `CARD_BG`, `TEXT_WHITE`) will be ported directly into the Streamlit dashboard layout and custom CSS.

---

## 4. Component Breakdown & Target Directory Structure

```
Netflix-Live-Content-Analytics/
├── config/
│   ├── __init__.py
│   └── settings.py                 # Centralized Pydantic BaseSettings & env loader
├── data/
│   ├── raw/                        # Ingested raw batch dumps (timestamped)
│   ├── processed/                  # Cleaned intermediate artifacts
│   ├── netflix_titles.csv          # Original baseline raw dataset
│   └── netflix_cleaned.csv         # Original baseline cleaned dataset
├── database/
│   ├── __init__.py
│   ├── database.py                 # SQLAlchemy engine, session factory, base
│   ├── models.py                   # NetflixContent ORM model mapping
│   └── repository.py               # Data access layer for analytics & ingestion
├── pipeline/
│   ├── __init__.py
│   ├── data_sources/
│   │   ├── __init__.py
│   │   ├── base_source.py          # Abstract BaseDataSource
│   │   ├── csv_source.py           # CSV file & incremental simulation source
│   │   └── api_source.py           # Configurable REST API data source
│   ├── fetch_data.py               # Extract stage orchestrator
│   ├── validate_data.py            # Schema validation & type checking
│   ├── clean_data.py               # Text cleaning & missing value imputation
│   ├── transform_data.py           # Feature engineering & duration/date parsing
│   ├── deduplicate.py              # Primary key & duplicate detection engine
│   ├── load_data.py                # Database loader & upsert manager
│   └── pipeline_runner.py          # Master ETL orchestrator returning status metrics
├── analytics/
│   ├── __init__.py
│   ├── overview.py                 # High-level KPIs & catalog totals
│   ├── content_analysis.py         # Movies vs TV Shows proportions & ratios
│   ├── country_analysis.py         # Top countries & international co-productions
│   ├── genre_analysis.py           # Genre distributions & category rankings
│   ├── trend_analysis.py           # Yearly addition trends, release lag, seasonality
│   ├── rating_analysis.py          # MPAA ratings & age-demographic breakdowns
│   ├── people_analysis.py          # Prolific directors & leading actors
│   └── duration_analysis.py        # Movie runtimes & TV Show season distributions
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entrypoint & middleware
│   └── api/
│       ├── __init__.py
│       ├── overview.py             # GET /api/overview
│       ├── content.py              # GET /api/content-distribution
│       ├── countries.py            # GET /api/top-countries
│       ├── genres.py               # GET /api/top-genres
│       ├── trends.py               # GET /api/content-growth, GET /api/monthly-additions
│       ├── ratings.py              # GET /api/rating-distribution
│       ├── people.py               # GET /api/top-directors, GET /api/top-actors
│       ├── duration.py             # GET /api/movie-duration, GET /api/tv-seasons
│       └── pipeline.py             # POST /api/refresh-data, GET /api/pipeline-status
├── dashboard/
│   ├── __init__.py
│   ├── app.py                      # Main Streamlit dashboard application
│   ├── components/
│   │   ├── __init__.py
│   │   ├── kpi_cards.py            # Modular KPI card renderers
│   │   ├── charts.py               # Plotly & Matplotlib chart renderers
│   │   └── filters.py              # Sidebar filter widgets
│   └── styles/
│       └── custom.css              # Custom Netflix dark-theme CSS injection
├── scheduler/
│   ├── __init__.py
│   └── scheduler.py                # APScheduler background runner for auto updates
├── tests/
│   ├── __init__.py
│   ├── test_validation.py          # Test schema validation & rejection
│   ├── test_cleaning.py            # Test text stripping & imputation
│   ├── test_deduplication.py       # Test duplicate detection & collision logic
│   ├── test_database.py            # Test ORM models & repository queries
│   ├── test_analytics.py           # Test analytical aggregations & KPIs
│   └── test_api.py                 # Test FastAPI endpoints with TestClient
├── docs/
│   ├── existing_project_analysis.md# Phase 1 deep-dive analysis
│   ├── implementation_plan.md      # This implementation plan
│   └── architecture.md             # System architecture & component interaction guide
├── logs/                           # Automated rotating log files
├── notebooks/                      # Retained original Jupyter notebooks
├── reports/                        # Retained original static business reports
├── src/                            # Retained original modules for backward compatibility
├── visualizations/                 # Retained original 12 static PNGs
├── .env.example                    # Environment configuration template
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Upgraded production dependencies
└── README.md                       # Comprehensive portfolio README
```

---

## 5. Data Pipeline Design (ETL)

### 5.1 Extract (`pipeline/data_sources/` & `pipeline/fetch_data.py`)
- **Abstract Base Class**: `BaseDataSource` with abstract methods:
  - `fetch_records() -> pd.DataFrame`
  - `get_metadata() -> dict`
- **Implementations**:
  - `CSVDataSource`: Reads from a CSV file path. Can run in full mode or simulated incremental batch mode (slicing batches of new titles to simulate real-world streaming updates).
  - `APIDataSource`: Pulls JSON from a remote REST API or mock service with timeout handling and error recovery.
- **Raw Storage**: Ingested raw batches are archived in `data/raw/batch_<timestamp>.csv` for auditability and lineage tracking.

### 5.2 Validate (`pipeline/validate_data.py`)
- Verifies presence of mandatory columns (`show_id`, `type`, `title`).
- Checks data types: `release_year` must be integer-convertible; `show_id` must be non-empty.
- Detects invalid records (e.g. missing titles, corrupt characters) and quarantines them.
- Returns a tuple `(valid_df, invalid_df, validation_report)`.

### 5.3 Clean (`pipeline/clean_data.py`)
- Applies unicode cleanup, whitespace trimming, and string normalization (`clean_text_formatting`).
- Strategically imputes missing values (`"Unknown Director"`, `"Unknown Cast"`, `"Unknown Country"`, `"Unavailable"`).
- Sets missingness tracking flags (`has_director_info`, `has_cast_info`, `has_country_info`, `has_date_added`).

### 5.4 Transform (`pipeline/transform_data.py`)
- Parses `date_added` into ISO timestamp.
- Extracts `year_added`, `month_added`, `month_name_added`, `day_added`, and `release_to_add_lag`.
- Parses numerical `duration_min` for movies and `seasons` for TV shows.
- Computes `movie_duration_tier` bins.
- Maps maturity ratings into 5 demographic tiers (`age_group`).
- Extracts multi-value features: `primary_country`, `country_count`, `is_multi_country`, `primary_genre`, `genre_count`, `cast_count`.

### 5.5 Deduplicate (`pipeline/deduplicate.py`)
- Compares incoming records against both the current batch and the active database:
  1. Internal batch deduplication: Deduplicates on `show_id` and subset `["title", "type", "release_year"]`.
  2. Database collision detection: Queries existing `show_id` values in `netflix_content`.
  3. Action classification:
     - New Records: Ingested into database.
     - Duplicates: Skipped and logged.
     - Existing Records with changes: Optional update/upsert.
- Generates an ingestion summary:
  ```json
  {
    "received": 500,
    "valid": 490,
    "invalid": 10,
    "new_inserted": 45,
    "duplicates_skipped": 445
  }
  ```

### 5.6 Load (`pipeline/load_data.py`)
- Executes atomic bulk insertion using SQLAlchemy ORM / bulk insert mappings.
- Manages transactions with rollback on failure.

### 5.7 Master Pipeline Runner (`pipeline/pipeline_runner.py`)
- Coordinates: `fetch -> validate -> clean -> transform -> deduplicate -> load`.
- Logs execution progress with timestamps.
- Returns structured pipeline metrics.

---

## 6. Database Design

### 6.1 Database Engine
- **Engine**: SQLite by default for zero-setup local execution (`data/netflix_live.db`).
- **ORM**: SQLAlchemy 2.0+ enabling effortless migration to PostgreSQL (`postgresql+psycopg2://...`) via configuration.
- **Connection**: Managed session factory with connection pooling and scoped sessions.

### 6.2 Table Schema: `netflix_content`
```sql
CREATE TABLE netflix_content (
    show_id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    director TEXT,
    cast TEXT,
    country TEXT,
    date_added DATE,
    release_year INTEGER,
    rating VARCHAR(50),
    duration VARCHAR(50),
    listed_in TEXT,
    description TEXT,
    year_added INTEGER,
    month_added INTEGER,
    month_name_added VARCHAR(20),
    day_added INTEGER,
    release_to_add_lag FLOAT,
    duration_min FLOAT,
    seasons INTEGER,
    movie_duration_tier VARCHAR(50),
    age_group VARCHAR(50),
    has_director_info BOOLEAN,
    has_cast_info BOOLEAN,
    has_country_info BOOLEAN,
    has_date_added BOOLEAN,
    primary_country VARCHAR(100),
    country_count INTEGER,
    is_multi_country BOOLEAN,
    primary_genre VARCHAR(100),
    genre_count INTEGER,
    cast_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_netflix_type ON netflix_content(type);
CREATE INDEX idx_netflix_release_year ON netflix_content(release_year);
CREATE INDEX idx_netflix_year_added ON netflix_content(year_added);
CREATE INDEX idx_netflix_rating ON netflix_content(rating);
CREATE INDEX idx_netflix_primary_country ON netflix_content(primary_country);
```

### 6.3 Repository Pattern (`database/repository.py`)
- `get_all_content(filters: dict) -> pd.DataFrame`
- `get_content_by_id(show_id: str) -> Optional[NetflixContent]`
- `get_total_counts() -> dict`
- `get_existing_show_ids() -> set[str]`
- `insert_records(records: list[dict]) -> int`
- `upsert_records(records: list[dict]) -> int`

---

## 7. Analytics Engine Design

The `analytics/` package decouples data calculations from any presentation framework:
- **`overview.py`**: Total catalog count, movie count, TV show count, unique countries, unique genres, earliest/latest release years, latest addition date.
- **`content_analysis.py`**: Content type distribution, percentage share, ratio of Movies to TV Shows.
- **`country_analysis.py`**: Top N countries (unnested and primary), percentage of catalog, co-production statistics.
- **`genre_analysis.py`**: Top overall genres, movie genres vs TV genres, average genres per title.
- **`trend_analysis.py`**: Yearly additions (2008–present), annual release trajectory, monthly seasonality (January–December), licensing lag distribution.
- **`rating_analysis.py`**: Maturity rating distribution, Movie vs TV Show rating breakdown, 5-tier audience demographic clustering.
- **`people_analysis.py`**: Top 15 prolific directors, top 15 global actors, regional actor breakdowns (India, US, UK).
- **`duration_analysis.py`**: Movie runtime statistics (mean, median, std, IQR), duration tiers, TV show seasons breakdown (1-season, 2-season, 3+ seasons, longest running).

All analytics functions accept optional filter arguments (`content_type`, `min_year`, `max_year`, `country`, `genre`) to support dynamic dashboard drill-downs.

---

## 8. Backend API Design (FastAPI)

### 8.1 API Endpoints Specification
| Method | Path | Description | Response Model / Payload |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status | `{"status": "ok", "db_connected": true}` |
| `GET` | `/api/overview` | Platform KPI metrics | `{"total_content": 5834, "total_movies": 3937, "total_tv_shows": 1897, ...}` |
| `GET` | `/api/content-distribution` | Movies vs TV Shows breakdown | `{"labels": ["Movie", "TV Show"], "values": [3937, 1897], "percentages": [67.48, 32.52]}` |
| `GET` | `/api/top-countries` | Top producing countries | `{"countries": ["United States", "India", ...], "counts": [2421, 752, ...]}` |
| `GET` | `/api/top-genres` | Top content categories | `{"genres": ["International Movies", "Dramas", ...], "counts": [...]}` |
| `GET` | `/api/content-growth` | Annual additions trajectory | `{"years": [2008, 2009, ...], "movies": [...], "tv_shows": [...], "totals": [...]}` |
| `GET` | `/api/monthly-additions` | Monthly addition seasonality | `{"months": ["January", "February", ...], "counts": [...]}` |
| `GET` | `/api/rating-distribution` | Content ratings and demographics | `{"ratings": [...], "age_groups": [...], "type_breakdown": {...}}` |
| `GET` | `/api/top-directors` | Top directors by title count | `{"directors": [...], "counts": [...]}` |
| `GET` | `/api/top-actors` | Top actors by appearances | `{"global": [...], "india": [...], "us": [...]}` |
| `GET` | `/api/movie-duration` | Runtime statistics and tiers | `{"stats": {"mean": 97.0, "median": 97.0, ...}, "tiers": [...]}` |
| `GET` | `/api/tv-seasons` | Season count distributions | `{"seasons": [...], "counts": [...], "single_season_pct": 67.4}` |
| `POST`| `/api/refresh-data` | Trigger manual ETL pipeline | `{"status": "success", "summary": {...}}` |
| `GET` | `/api/pipeline-status` | Latest pipeline execution report | `{"last_run": "2026-08-30T...", "records_processed": 5834, ...}` |
| `POST`| `/api/simulate-batch` | Inject simulated batch of new data | `{"injected_count": 10, "new_records": 10}` |

---

## 9. Interactive Dashboard Design (Streamlit)

### 9.1 Theme & Visual Styling
- Custom CSS injected with signature Netflix styling:
  - Background: `#141414` (Dark Charcoal)
  - Cards: `#1F1F1F` (Elevated Charcoal) with subtle crimson borders
  - Primary Brand Red: `#E50914`
  - Text: `#FFFFFF` (High contrast) and `#B3B3B3` (Secondary)
  - Accents: Gold `#F5A623` and Cyan `#00E5FF`

### 9.2 Dashboard Layout
1. **Header & Live Control Bar**:
   - Platform branding with dynamic status indicator ("🟢 Database Live").
   - Metrics: Database record count, Last Pipeline Run timestamp.
   - **"🔄 Refresh Pipeline Data"** button triggering the ETL run with instantaneous feedback.
   - **"🎲 Ingest Simulated New Batch"** button demonstrating dynamic streaming ingestion.
2. **Sidebar Filters**:
   - Content Type Selector (All, Movie, TV Show).
   - Release Year Range Slider (1925 – 2024).
   - Country Multi-Select Filter.
   - Genre Multi-Select Filter.
3. **KPI Metrics Cards**:
   - Total Titles
   - Total Movies
   - Total TV Shows
   - Global Producing Countries
   - Distinct Content Categories
   - Median Movie Duration
4. **Visual Analytics Sections (Tabs / Sections)**:
   - **Section 1: Catalog Overview & Distribution**: Movies vs TV Shows Donut Chart, Catalog Ratio, Content Addition Velocity.
   - **Section 2: Geographic Footprint**: Top 10 Producing Countries, International Co-production Rate.
   - **Section 3: Genres & Categories**: Top 10 Genres, Movie vs TV Genre Comparison.
   - **Section 4: Temporal Growth & Seasonality**: Historical Additions (2008–2019+), Additions by Month Seasonality.
   - **Section 5: Maturity Ratings & Demographics**: Rating Distribution by Type, Target Demographic Breakdown.
   - **Section 6: Creators & Cast (Talent)**: Top 10 Prolific Directors, Top 10 Global & Regional Actors.
   - **Section 7: Runtime & Longevity**: Movie Runtime Histogram (Mean/Median markers), TV Show Season Count Distribution.
   - **Section 8: Multi-Variate Matrix**: Genre vs Rating Demographic Heatmap.
   - **Section 9: Live Data Explorer & Pipeline Logs**: Filterable data table and pipeline execution logs.

---

## 10. Automation & Refresh Architecture

### 10.1 Manual Refresh Flow
1. User clicks **"Refresh Data"** in the Streamlit UI (or calls `POST /api/refresh-data`).
2. Backend invokes `pipeline/pipeline_runner.py`.
3. Pipeline reads the latest data source, runs validation, cleans, transforms, checks duplicates against the DB, and commits new rows.
4. Streamlit cache clears and dashboard updates immediately with zero downtime.

### 10.2 Scheduled Refresh Flow
1. Background worker `scheduler/scheduler.py` runs using APScheduler.
2. Schedule frequency read from `UPDATE_FREQUENCY` environment variable (`HOURLY`, `DAILY`, `WEEKLY`, `INTERVAL_SECONDS=...`, or `MANUAL`).
3. Executes `run_pipeline()`, logs results to `logs/pipeline.log`, and triggers notification callbacks.

---

## 11. Configuration & Logging

### 11.1 Configuration (`config/settings.py`)
- Managed using `pydantic-settings` or `os.getenv` with sensible defaults:
  - `DATABASE_URL`: `sqlite:///data/netflix_live.db`
  - `DATA_SOURCE_TYPE`: `csv` (or `api`)
  - `DATA_SOURCE_PATH`: `data/netflix_titles.csv`
  - `API_HOST`: `127.0.0.1`
  - `API_PORT`: `8000`
  - `UPDATE_FREQUENCY`: `MANUAL`
  - `LOG_LEVEL`: `INFO`
- Accompanied by `.env.example`.

### 11.2 Logging Architecture
- Python `logging` module configured with format: `%(asctime)s [%(levelname)s] [%(name)s]: %(message)s`.
- Outputs both to console and rotating log files in `logs/platform.log`.

---

## 12. Testing Strategy

Comprehensive automated tests implemented with `pytest` in `tests/`:
1. `test_validation.py`: Verifies column requirement checks, rejection of missing keys, and schema enforcement.
2. `test_cleaning.py`: Verifies whitespace cleanup, imputation of missing fields, and date/duration parsing.
3. `test_deduplication.py`: Verifies duplicate detection logic on duplicate IDs and subset collisions.
4. `test_database.py`: Tests SQLAlchemy database creation, record insertion, querying, and repository methods.
5. `test_analytics.py`: Validates KPI counts, content percentages, country aggregations, and runtime statistics.
6. `test_api.py`: Uses FastAPI's `TestClient` to verify all REST endpoints return HTTP 200 and expected JSON schemas.

---

## 13. Step-by-Step Execution Sequence

1. **Step 1: Inspect existing project** (Completed - `docs/existing_project_analysis.md`).
2. **Step 2: Create implementation plan** (Completed - `docs/implementation_plan.md` & planning mode artifact).
3. **Step 3: Establish environment and dependencies** (`requirements.txt`, `.env.example`, `config/settings.py`).
4. **Step 4: Build database layer** (`database/database.py`, `database/models.py`, `database/repository.py`).
5. **Step 5: Build modular data source layer** (`pipeline/data_sources/`).
6. **Step 6: Build ETL pipeline stages** (`fetch_data`, `validate_data`, `clean_data`, `transform_data`, `deduplicate`, `load_data`, `pipeline_runner`).
7. **Step 7: Seed database with existing dataset and verify integrity**.
8. **Step 8: Build modular analytics services** (`analytics/`).
9. **Step 9: Build FastAPI backend & REST routers** (`backend/main.py`, `backend/api/`).
10. **Step 10: Build interactive Streamlit dashboard** (`dashboard/app.py`, components, styling).
11. **Step 11: Implement refresh mechanisms** (manual button & APScheduler background runner).
12. **Step 12: Add test suite and run pytest**.
13. **Step 13: Update README.md and documentation**.
14. **Step 14: End-to-end platform verification**.
