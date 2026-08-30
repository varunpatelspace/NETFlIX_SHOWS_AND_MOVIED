# System Architecture & Layered Component Guide

This document defines the 10 architectural layers comprising the **Netflix Live Content Analytics Platform**, detailing responsibilities, modules, data contracts, and dependency graphs.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 10: Deployment                     │
│           (Docker, Docker Compose, Volume Storage)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Layer 9: Automation                     │
│      (APScheduler, SourceMonitor, Concurrency Lock, Jobs)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌──────────────────────────────┐       ┌──────────────────────────────┐
│     Layer 8: Dashboard       │       │        Layer 7: API          │
│   (Streamlit, Plotly, UI)    │       │    (FastAPI REST Endpoints)  │
└──────────────┬───────────────┘       └──────────────┬───────────────┘
               │                                      │
               └───────────────────┬──────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                     Layer 6: Analytics                      │
│        (AnalyticsService, Insights, Format Analytics)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Layer 5: Repository                     │
│         (NetflixRepository, Dynamic Filter Queries)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Layer 4: Database                      │
│        (SQLAlchemy ORM, Engine, SessionLocal, Models)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        Layer 3: ETL                         │
│   (Fetch → Validate → Clean → Transform → Dedupe → Load)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 2: Data Sources                    │
│        (CSVDataSource, APIDataSource, DataSourceFactory)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Layer 1: Configuration                    │
│       (config/settings.py, config/logging_config.py, .env)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Layer Specifications

### 1. Configuration Layer
* **Responsibility**: Centralizes platform-wide configuration, path resolution, environment variable defaults, and structured logging initialization.
* **Main Modules**:
  - `config/settings.py`: Resolves database URLs, port mappings, data paths, and scheduler flags.
  - `config/logging_config.py`: Initializes dedicated log handlers for `application.log`, `pipeline.log`, and `scheduler.log`.
* **Inputs**: Environment variables (`.env`, OS environment).
* **Outputs**: Strongly typed constants and logging singletons.
* **Dependencies**: Python standard library (`os`, `pathlib`, `logging`).

---

### 2. Data Source Layer
* **Responsibility**: Provides an extensible abstraction for ingesting raw data from heterogeneous upstream systems without coupling the pipeline to file formats.
* **Main Modules**:
  - `pipeline/data_sources/base_source.py`: `BaseDataSource` abstract base class.
  - `pipeline/data_sources/csv_source.py`: Primary streaming and batched CSV reader.
  - `pipeline/data_sources/api_source.py`: REST API data source adapter.
  - `pipeline/data_sources/factory.py`: `DataSourceFactory` resolving sources dynamically.
* **Inputs**: File system paths or remote HTTP URLs.
* **Outputs**: Raw pandas DataFrames accompanied by extraction metadata.
* **Dependencies**: `pandas`, Configuration Layer.

---

### 3. ETL Pipeline Layer
* **Responsibility**: Orchestrates data validation, text normalization, feature engineering, payload standardization, two-tier deduplication, and database insertion.
* **Main Modules**:
  - `pipeline/fetch_data.py`: Extraction wrapper.
  - `pipeline/validate_data.py`: Schema enforcement & row anomaly isolation.
  - `pipeline/clean_data.py`: Missingness imputation & 19 derived features.
  - `pipeline/transform_data.py`: ISO standardizer & dictionary packaging.
  - `pipeline/deduplicate.py`: Level A (batch) & Level B (database) deduplication.
  - `pipeline/load_data.py`: Transactional database persistence.
  - `pipeline/pipeline_runner.py`: Master 6-stage pipeline executor.
* **Inputs**: Raw data from Data Source Layer.
* **Outputs**: Structured execution receipts (`PipelineExecutionReport`) with record counts and duration.
* **Dependencies**: Data Source Layer, Database Layer, Repository Layer.

---

### 4. Database Layer
* **Responsibility**: Defines relational schemas, manages database connection pooling, handles transactional sessions, and ensures cross-database compatibility (SQLite / PostgreSQL).
* **Main Modules**:
  - `database/database.py`: SQLAlchemy `engine`, `SessionLocal`, and `init_db()`.
  - `database/models.py`: ORM entities (`NetflixContent`, `PipelineRun`, `SourceState`).
* **Inputs**: Database connection string (`DATABASE_URL`).
* **Outputs**: Active SQLAlchemy sessions and query cursors.
* **Dependencies**: `sqlalchemy`.

---

### 5. Repository Layer
* **Responsibility**: Encapsulates all SQL query generation, dynamic filtering, multi-column search, and CRUD operations away from business logic.
* **Main Modules**:
  - `database/repository.py`: `NetflixRepository` providing parameterized queries (`get_all`, `get_by_id`, `get_filtered_dataframe`, `upsert_batch`).
* **Inputs**: Session instances and filter parameters (`content_type`, `year`, `genre`, etc.).
* **Outputs**: Model instances, counts, and pandas DataFrames.
* **Dependencies**: Database Layer.

---

### 6. Analytics Layer
* **Responsibility**: Computes descriptive statistics, distributions, growth trends, format ratios, and evidence-based observational business insights.
* **Main Modules**:
  - `analytics/analytics_service.py`: Central facade coordinating domain analyzers.
  - `analytics/overview.py`: High-level KPI calculations.
  - `analytics/content_analysis.py`: Movies vs TV Shows and genre distributions.
  - `analytics/temporal_analysis.py`: Additions by year, seasonality, and licensing lag.
  - `analytics/geographic_analysis.py`: Producing territories and co-productions.
  - `analytics/rating_analysis.py`: Maturity certifications and 5-tier audience age groups.
  - `analytics/duration_analysis.py`: Film runtimes and TV series longevity.
  - `analytics/insights.py`: Rule-based observational insight generator.
* **Inputs**: Filter parameters and active database sessions.
* **Outputs**: Clean JSON-serializable dictionaries containing labels, values, and metrics.
* **Dependencies**: Repository Layer, `pandas`, `numpy`.

---

### 7. API Backend Layer
* **Responsibility**: Exposes platform metrics, catalog explorer endpoints, pipeline controls, and system health checks over a RESTful HTTP interface with OpenAPI schemas.
* **Main Modules**:
  - `api/main.py`: FastAPI application, CORS middleware, lifespan context manager.
  - `api/routes/health.py`: System health check (`GET /health`).
  - `api/routes/analytics.py`: Domain metrics & master dashboard summary.
  - `api/routes/content.py`: Paginated title search & inspection (`GET /content`).
  - `api/routes/pipeline.py`: Ingestion status, on-demand refresh, audit history, automation status.
  - `api/schemas/`: Pydantic request/response models.
* **Inputs**: HTTP requests, query parameters, JSON payloads.
* **Outputs**: HTTP responses with JSON bodies and standard status codes.
* **Dependencies**: Analytics Layer, Pipeline Layer, Automation Layer, `fastapi`, `uvicorn`, `pydantic`.

---

### 8. Dashboard Presentation Layer
* **Responsibility**: Delivers an interactive, Netflix-themed web UI for business intelligence, demographic drill-down, catalog exploration, and pipeline administration.
* **Main Modules**:
  - `dashboard/app.py`: Main landing page (Executive Overview).
  - `dashboard/pages/`: Multi-page apps (Overview, Content, Temporal, Geographic, Ratings, Duration, Explorer, Data Management).
  - `dashboard/components/api_client.py`: Decoupled HTTP API client.
  - `dashboard/components/styling.py`: Custom Netflix dark mode CSS and cards.
  - `dashboard/components/filters.py`: Persistent sidebar filters.
  - `dashboard/components/charts.py`: Reusable Plotly chart constructors.
* **Inputs**: User UI interactions and filter selections.
* **Outputs**: Rendered HTML, CSS, and interactive SVG/WebGL charts.
* **Dependencies**: API Layer (via HTTP), `streamlit`, `plotly`, `requests`.

---

### 9. Automation & Scheduling Layer
* **Responsibility**: Manages background scheduled data syncs, computes cryptographic source fingerprints to eliminate redundant ETL runs, prevents concurrency conflicts, and persists run audit logs.
* **Main Modules**:
  - `automation/scheduler.py`: Singleton `BackgroundScheduler` lifecycle.
  - `automation/jobs.py`: Concurrency-guarded execution wrapper (`_pipeline_lock`).
  - `automation/source_monitor.py`: SHA-256 source state detector.
  - `automation/pipeline_monitor.py`: Persistent audit logging to `pipeline_runs`.
* **Inputs**: Configured update intervals, source files, and database states.
* **Outputs**: Automated ingestion triggers and audit records.
* **Dependencies**: Pipeline Layer, Database Layer, `apscheduler`.

---

### 10. Deployment Layer
* **Responsibility**: Packages the frontend and backend into lightweight, portable, reproducible OCI container images orchestrated via Docker Compose with volume persistence and health checks.
* **Main Modules**:
  - `Dockerfile.api`: Python 3.11 slim image running Uvicorn.
  - `Dockerfile.dashboard`: Python 3.11 slim image running Streamlit.
  - `docker-compose.yml`: Multi-service orchestration with persistent volumes.
  - `.dockerignore`: Context filter preventing artifact bloat.
* **Inputs**: Repository source code and Docker engine.
* **Outputs**: Running container instances on ports 8000 and 8501.
* **Dependencies**: Docker Engine, Docker Compose.
