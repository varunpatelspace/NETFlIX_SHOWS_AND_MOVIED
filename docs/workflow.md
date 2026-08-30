# End-to-End Operational Workflow: Automated Ingestion Scenario

This document walks through a realistic end-to-end scenario demonstrating how the **Netflix Live Content Analytics Platform** autonomously detects new catalog records, executes conditional ETL, updates persistent storage, and delivers fresh analytics to the user interface.

---

## The Scenario

An upstream content provider drops an updated CSV file (`data/netflix_titles.csv`) containing 10 newly licensed international movie and series releases.

---

## 16-Step Autonomous Execution Flow

```text
[1] Scheduler Wakeup
         │
         ▼
[2] Calculate SHA-256 Fingerprint
         │
         ▼
[3] Fingerprint Comparison (Mismatch Detected)
         │
         ▼
[4] Acquire Concurrency Lock & Initialize PipelineRun (RUNNING)
         │
         ▼
[5] Extract Raw Data via Factory
         │
         ▼
[6] Validate Schema Integrity & Quarantine Invalid Rows
         │
         ▼
[7] Clean Data (Whitespace Trim & Null Imputation)
         │
         ▼
[8] Engineer 19 Derivative Features
         │
         ▼
[9] Level A Deduplication (Batch Internal Title Collisions)
         │
         ▼
[10] Level B Deduplication (Database show_id Partitioning)
         │
         ▼
[11] Transactional Ingestion (Insert New / Upsert Changed)
         │
         ▼
[12] Commit Database Transaction
         │
         ▼
[13] Update SourceState & Finalize PipelineRun Audit Record
         │
         ▼
[14] Release Concurrency Lock
         │
         ▼
[15] Analytics Engine Computes Fresh Aggregates
         │
         ▼
[16] Dashboard & REST API Reflect New Catalog State
```

---

## Detailed Step Walkthrough

### 1. Scheduler Trigger
`APScheduler` executes `scheduled_refresh_job()` according to `UPDATE_FREQUENCY_SECONDS` (e.g. every 3600 seconds).

### 2. Fingerprint Computation
`SourceMonitor.compute_source_fingerprint()` reads the source CSV in 64KB chunks to calculate:
- Streaming SHA-256 Checksum: `ea000bb56cb3b031...`
- File Size: `2,241,890 bytes`
- Total Lines: `5,847 rows`

### 3. Change Detection
`SourceMonitor.has_source_changed()` queries `source_states` in SQLite. It compares the current checksum against the previous successful run.
- **Result**: Checksums differ (`prev != current`). The system determines that an ETL execution is required.

### 4. Concurrency Guard & Audit Initiation
- `jobs._pipeline_lock.acquire(blocking=False)` is executed. If another execution were running, it would exit cleanly with `CONCURRENCY_CONFLICT`.
- `PipelineMonitor.start_run()` creates a record in `pipeline_runs` with `status="RUNNING"`, `run_id="pipe_7ec1c087"`, and `started_at=NOW()`.

### 5. Extraction
`DataSourceFactory.get_data_source("csv")` streams the raw records into memory as a clean pandas DataFrame with extraction metadata.

### 6. Validation
`DataValidator.validate()` enforces schema integrity:
- Checks required critical columns (`show_id`, `type`, `title`, `release_year`).
- Any corrupt or null-key row is quarantined into `data/raw/quarantine_*.csv`.
- Valid records continue downstream.

### 7. Cleaning
`DataCleaner.clean()` applies standardized cleaning rules:
- Strips leading and trailing whitespaces across all text columns.
- Imputes missing directors with `"Not Listed"`.
- Imputes missing cast with `"Not Listed"`.
- Imputes missing countries with `"Unknown"`.

### 8. Feature Engineering
The pipeline derives 19 structured features:
- `duration_min`: Parsed integer runtime (e.g. `"110 min"` -> `110.0`).
- `seasons`: Parsed integer season count (e.g. `"3 Seasons"` -> `3`).
- `age_group`: Demographic classification (`"Adults (18+)"`, `"Teens (13-17)"`, etc.).
- `movie_duration_tier`: Categorization into runtime buckets.
- `release_to_add_lag`: Latency between premiere year and catalog addition year.

### 9. Level A Deduplication (Batch Internal)
Scans the incoming batch for internal duplicate combinations of `title + type + release_year`. If found, keeps the earliest record and records duplicates.

### 10. Level B Deduplication (Database Collision Check)
Queries existing database IDs via `NetflixRepository.get_all_ids()`:
- Categorizes records into **Genuinely New** (10 records) and **Pre-Existing in DB** (5,834 records).

### 11. Transactional Load & Ingestion
Executes `load_data()` within an active SQLAlchemy transaction (`session.begin()`):
- **If mode is `insert_new_only`**: Directly inserts the 10 new titles; skips the 5,834 existing titles.
- **If mode is `upsert`**: Inserts the 10 new titles and updates modified attributes for existing titles.

### 12. Transaction Commit
The database transaction commits successfully. If any error had occurred, `session.rollback()` would have been invoked immediately.

### 13. Audit & State Finalization
- `SourceMonitor.record_successful_source_state()` updates `source_states` with the new SHA-256 fingerprint and timestamp.
- `PipelineMonitor.finish_run()` updates `pipeline_runs`:
  - `status="SUCCESS"`
  - `inserted=10`
  - `updated=0`
  - `skipped=5834`
  - `execution_duration=0.85s`

### 14. Lock Release
In the `finally` block, `_pipeline_lock.release()` clears the active process lock.

### 15. Analytics Ingestion
Next time an analytics query is executed, `AnalyticsService` queries the updated database, reflecting the 10 new titles across format ratios, genre counts, and temporal charts.

### 16. User Interface Reflection
- Users on the **Streamlit Dashboard** see updated KPIs (Total Titles: 5,844).
- The **Data Management Page** displays the new successful pipeline run in the audit ledger with a green `SUCCESS` badge.
- The **Content Explorer** immediately surfaces the 10 new titles via keyword search.
