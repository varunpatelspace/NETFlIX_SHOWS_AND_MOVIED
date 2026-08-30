# Automated Testing & Verification Suite Documentation

The **Netflix Live Content Analytics Platform** incorporates an exhaustive automated testing suite with **50 unit and integration tests** spanning 8 test modules.

To execute the complete test suite:
```bash
python -m pytest tests/ -v
```

---

## 1. Test Suite Summary

```text
tests/test_analytics.py                9 passed [ 18%]
tests/test_api.py                      9 passed [ 36%]
tests/test_automation.py               7 passed [ 50%]
tests/test_dashboard.py                5 passed [ 60%]
tests/test_data_sources.py             6 passed [ 72%]
tests/test_database.py                 3 passed [ 78%]
tests/test_incremental_hardening.py    4 passed [ 86%]
tests/test_pipeline.py                 7 passed [100%]
======================== 50 passed in 4.81s ========================
```

---

## 2. Test Module Breakdown

### 1. Database Layer (`tests/test_database.py` - 3 Tests)
* `test_insert_and_query_record`: Validates entity mapping, primary key generation, and timestamp creation in SQLite.
* `test_upsert_logic`: Tests record attribute modification, verifying that updates modify existing records rather than duplicating rows.
* `test_dataframe_retrieval`: Validates SQL-to-Pandas DataFrame conversion with type integrity.

### 2. Data Sources Layer (`tests/test_data_sources.py` - 6 Tests)
* `test_csv_data_source_with_existing_dataset`: Verifies reading 5,837 rows from `netflix_titles.csv`.
* `test_csv_data_source_batching`: Verifies streaming ingestion chunk by chunk.
* `test_csv_data_source_missing_file`: Verifies `FileNotFoundError` is cleanly caught.
* `test_csv_data_source_empty_file`: Verifies handling of 0-byte CSV files.
* `test_api_data_source_with_mock_payload`: Validates parsing of JSON payloads from API sources.
* `test_data_source_factory`: Tests resolution of CSV vs API sources via `DataSourceFactory`.

### 3. ETL Pipeline Layer (`tests/test_pipeline.py` - 7 Tests)
* `test_validation_fatal_missing_critical_column`: Verifies `DataValidationError` when critical columns (`show_id`, `type`, `title`) are missing.
* `test_validation_fatal_empty_dataset`: Verifies rejection of empty datasets.
* `test_validation_row_level_quarantine`: Tests isolation of rows with missing IDs into quarantine partitions.
* `test_cleaning_and_transformation_pipeline`: Verifies generation of 19 derived features (`duration_min`, `seasons`, `age_group`, `movie_duration_tier`, etc.).
* `test_two_level_deduplication`: Verifies Level A (batch internal) and Level B (database collision) deduplication.
* `test_pipeline_runner_idempotency`: Verifies that executing the pipeline twice against identical data produces 0 duplicate records.
* `test_pipeline_failure_handling_missing_file`: Verifies safe failure reporting when source files are absent.

### 4. Incremental Update Hardening (`tests/test_incremental_hardening.py` - 4 Tests)
* `test_incremental_lifecycle`: Tests Scenarios A, B, and C (initial insert -> zero duplicates on re-run -> incremental additions of new rows).
* `test_changed_metadata_modes`: Tests behavior when existing `show_id` records have changed metadata:
  - Mode `insert_new_only`: Skips existing record; preserves database state.
  - Mode `upsert`: Updates existing record with fresh metadata.
* `test_conflicting_internal_show_id_resolution`: Tests deterministic resolution when incoming batch contains duplicate `show_id` keys with conflicting titles.
* `test_transaction_rollback_on_simulated_db_failure`: Validates database rollback and consistency during mid-batch database exceptions.

### 5. Analytics Engine (`tests/test_analytics.py` - 9 Tests)
* `test_overview_metrics`: Tests calculation of total titles, movie/TV percentages, and country counts.
* `test_content_type_analysis`: Tests movie vs TV distributions and top genre rankings.
* `test_temporal_analysis`: Tests yearly addition trends, release distributions, and licensing lag calculations.
* `test_geographic_analysis`: Tests top producing countries and international co-production ratios.
* `test_rating_analysis`: Tests maturity certification distribution and 5-tier audience age group mappings.
* `test_duration_analysis`: Tests movie runtime percentiles (mean, median, IQR) and TV show season longevity.
* `test_analytics_filtering`: Validates multi-dimensional SQL query filtering by country, genre, year, and rating.
* `test_insights_generation`: Tests generation of evidence-based observational business insights.
* `test_empty_database_safety`: Validates that querying an empty database returns safe zero/empty structures rather than exceptions.

### 6. REST API Layer (`tests/test_api.py` - 9 Tests)
* `test_health_endpoint`: Tests `GET /health` responding with 200 OK and database connectivity status.
* `test_dashboard_summary_endpoint`: Tests `GET /api/v1/dashboard/summary`.
* `test_analytics_overview_and_filtering`: Tests parameterized query filtering over HTTP.
* `test_individual_analytics_endpoints`: Tests content, temporal, geographic, rating, and duration endpoints.
* `test_content_pagination`: Tests `GET /api/v1/content` pagination limits and offsets.
* `test_content_detail_found`: Tests `GET /api/v1/content/{show_id}` for existing title.
* `test_content_detail_not_found`: Tests 404 response for invalid `show_id`.
* `test_pipeline_status`: Tests `GET /api/v1/pipeline/status`.
* `test_pipeline_refresh_invalid_mode`: Tests 400 validation error when an unsupported mode is provided.

### 7. Streamlit Dashboard Components (`tests/test_dashboard.py` - 5 Tests)
* `test_api_client_initialization`: Tests base URL resolution and session pooling.
* `test_api_client_connection_error`: Tests graceful connection failure reporting when backend is offline.
* `test_api_client_query_param_construction`: Tests dictionary-to-query-parameter serialization.
* `test_api_client_refresh_pipeline_post`: Tests POST request execution and payload parsing.
* `test_plotly_chart_constructors`: Tests figure generation for donut, bar, line, and world map visualizers.

### 8. Automation & Scheduling Layer (`tests/test_automation.py` - 7 Tests)
* `test_source_monitor_first_fingerprint_and_unchanged`: Tests initial SHA-256 fingerprinting, unchanged state detection, and changed state detection on file update.
* `test_source_monitor_missing_source`: Tests missing source detection.
* `test_pipeline_monitor_lifecycle`: Tests run tracking from `RUNNING` to `SUCCESS` with duration and counts.
* `test_concurrency_protection`: Tests rejection (`HTTP 409 Conflict` / `CONCURRENCY_CONFLICT`) when an execution is already active.
* `test_persistence_across_sessions`: Tests that `PipelineRun` and `SourceState` records survive session recreation.
* `test_api_automation_endpoints`: Tests `/api/v1/automation/status` and `/api/v1/pipeline/history` endpoints.
* `test_scheduler_initialization_and_disabled_mode`: Tests scheduler disabled mode.

---

## 3. Test Invariant Guarantees
* **Isolated Testing**: All tests use temporary files and in-memory thread-safe SQLite databases (`StaticPool`), preventing interference with production data (`netflix_live.db`).
* **Zero Sleep Delays**: Automation tests simulate state changes deterministically without waiting for real-time timers.
* **Deterministic Rollback**: Every test cleans up its database sessions and temporary fixtures.
