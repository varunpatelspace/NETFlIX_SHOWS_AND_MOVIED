# End-to-End Data Flow & Lifecycle Specification

This document provides a comprehensive technical breakdown of how data moves through the **Netflix Live Content Analytics Platform**, from raw ingestion to interactive presentation.

---

## 1. High-Level Data Lifecycle Flowchart

```
┌─────────────────────────────────────────────────────────────┐
│                    Raw External Source                      │
│        (CSV File: data/netflix_titles.csv or Mock API)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Stage 1: Source Extraction                  │
│       (pipeline/data_sources/ & pipeline/fetch_data.py)     │
│   • Factory instantiates CSVDataSource / APIDataSource      │
│   • Extracts raw records, captures source metadata & clock  │
└──────────────────────────────┬──────────────────────────────┘
                               │ Raw DataFrame (5,837 rows)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Stage 2: Data Validation                    │
│               (pipeline/validate_data.py)                   │
│   • Fatal Validation: Schema integrity & required keys      │
│   • Row-Level Validation: Missing show_id, invalid dates    │
│   • Anomalies quarantined; valid records passed forward     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Validated DataFrame
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Stage 3: Cleaning & Feature Engineering           │
│                 (pipeline/clean_data.py)                    │
│   • Text Normalization: Whitespace trim, title-case format  │
│   • Imputation: Director, Cast, Country, Date Added defaults│
│   • Feature Engineering: 19 derived features (lag, age_group│
│     duration_min, seasons, movie_duration_tier, etc.)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ Cleaned DataFrame (31 columns)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Stage 4: Data Transformation                 │
│               (pipeline/transform_data.py)                  │
│   • Type Coercion: Integer years, float durations, booleans │
│   • Date Standardization: ISO format date strings           │
│   • Payload Packaging: Dictionary records matching ORM schema│
└──────────────────────────────┬──────────────────────────────┘
                               │ Transformed Payloads
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Stage 5: Two-Tier Deduplication              │
│                 (pipeline/deduplicate.py)                   │
│   • Level A (In-Batch): Deduplicate title+type+release_year │
│     and resolve conflicting incoming show_ids deterministically
│   • Level B (Database Collision): Check existing show_ids   │
│     Separate batch into genuinely new vs existing records   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Partitioned Ingestion Batch
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            Stage 6: Database Load & Incremental Sync        │
│          (pipeline/load_data.py & database/repository.py)   │
│   • Mode 'insert_new_only': Append new; skip existing       │
│   • Mode 'upsert': Overwrite changed metadata; append new   │
│   • Transactional Batching: Commit on success; safe rollback│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Relational Database Storage                  │
│                   (data/netflix_live.db)                    │
│   • netflix_content (Catalog entity, 31 indexed columns)    │
│   • pipeline_runs   (Execution audit ledger & metrics)      │
│   • source_states   (SHA-256 source state fingerprints)     │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│       Analytics Engine       │ │     Automation Layer       │
│        (analytics/)          │ │       (automation/)        │
│ • Aggregations & distributions│ │ • APScheduler periodic sync│
│ • 5-tier audience metrics    │ │ • SHA-256 change detection │
│ • Observational insights     │ │ • Concurrency process lock │
└──────────────┬───────────────┘ └─────────────┬──────────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Service                   │
│                        (api/main.py)                        │
│   • Pydantic validation, serialization, CORS middleware     │
│   • Endpoints: /health, /analytics/*, /content, /pipeline/* │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Interactive UI                    │
│                     (dashboard/app.py)                      │
│   • Executive Overview, 7 Analytics Pages, Content Explorer │
│   • Global Filters (Content Type, Year, Country, Genre, etc)│
│   • Live Pipeline Ingestion Trigger & Audit History Viewer  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Stage-by-Stage Processing Details

### Stage 1: Extraction (`pipeline/fetch_data.py`)
- **Factory Pattern**: Dynamically instantiates the appropriate data source reader (`CSVDataSource` or `APIDataSource`) via `DataSourceFactory.get_data_source()`.
- **Integrity Guarantee**: Reads raw data without mutating underlying files. Captures extraction timestamp, source name, and row/column counts in a metadata receipt.

### Stage 2: Validation (`pipeline/validate_data.py`)
- **Fatal Schema Checks**: Verifies required critical columns (`show_id`, `type`, `title`, `release_year`). If missing, raises `DataValidationError` immediately, halting the pipeline before database modification.
- **Row-Level Anomaly Quarantine**: Records missing required keys or invalid release years are isolated into a quarantined partition. Valid records continue through the pipeline without breaking downstream processing.

### Stage 3: Cleaning & Feature Engineering (`pipeline/clean_data.py`)
- **Imputation**:
  - `director` -> `"Not Listed"`
  - `cast` -> `"Not Listed"`
  - `country` -> `"Unknown"`
  - `date_added` -> Parsed to `datetime` or assigned conservative defaults
  - `rating` -> Mode imputation or `"Unrated"`
- **Derived Features (19 Columns)**:
  - `duration_min` & `seasons`: Parsed from raw strings (e.g. `"95 min"` -> `95.0`, `"2 Seasons"` -> `2`).
  - `movie_duration_tier`: Categorized into `<60m`, `60-90m`, `90-120m`, `120-150m`, `150m+`.
  - `age_group`: Categorized into `Little Kids (0-6)`, `Older Kids (7-12)`, `Teens (13-17)`, `Adults (18+)`, `Unrated`.
  - `primary_country` & `country_count`: Extracted from comma-separated strings; flags `is_multi_country`.
  - `primary_genre` & `genre_count`: Extracted from comma-separated `listed_in`.
  - `release_to_add_lag`: Difference between Netflix ingestion year and theatrical release year.

### Stage 4: Transformation (`pipeline/transform_data.py`)
- Coerces clean pandas structures into standardized typed Python dictionaries matching SQLAlchemy ORM schema definitions.
- Ensures all timestamps adhere to UTC ISO-8601 formatting.

### Stage 5: Deduplication (`pipeline/deduplicate.py`)
- **Level A (Batch Internal)**: Detects duplicate combinations of `title + type + release_year`. If multiple records share identical content keys, retains the first and logs duplicates. Resolves duplicate `show_id` instances in incoming batches deterministically.
- **Level B (Database Collision Check)**: Queries the database via `NetflixRepository.get_all_ids()` to identify which incoming records already exist in the database versus genuinely new titles.

### Stage 6: Database Load & Incremental Sync (`pipeline/load_data.py`)
- **Mode `insert_new_only`**:
  - Inserts only genuinely new `show_id` records.
  - Skips pre-existing titles, avoiding expensive database overwrites.
- **Mode `upsert`**:
  - Inserts new titles and updates attributes of existing records if source metadata has changed.
- **Transactional Safety**:
  - Batched insertion wraps operations in `session.begin()`.
  - Any failure triggers an automatic `session.rollback()`, ensuring database consistency is preserved.

---

## 3. Change Detection & Idempotent Ingestion

To prevent redundant and expensive data loads:
1. **Source Fingerprinting**: The `SourceMonitor` computes an initial SHA-256 hash across the entire source file alongside file size and row count.
2. **Comparison**: On scheduled runs, the hash is compared against `SourceState.checksum` stored in the database.
3. **Execution Decision**:
   - **Checksum Matched**: Ingestion is skipped. A `PipelineRun` record is created with `status="SKIPPED"` and `reason="Source unchanged since previous successful refresh"`.
   - **Checksum Changed / Missing**: The full incremental ETL pipeline executes, and upon successful completion, updates `SourceState` with the new fingerprint.

---

## 4. Analytics & Consumer Layer

- **Analytics Engine (`analytics/`)**: Reads directly from SQLite/PostgreSQL through `NetflixRepository`, computing catalog distributions, format ratios, temporal growth trajectories, and rule-based business insights.
- **FastAPI REST API (`api/`)**: Provides sub-15ms cached and parameterized query endpoints with full Pydantic validation and Swagger documentation.
- **Streamlit Dashboard (`dashboard/`)**: Decoupled presentation client communicating via HTTP `requests`, providing interactive Plotly visualizations and catalog browsing without holding direct database locks.
