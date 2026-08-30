# RESTful API Reference Guide

The **Netflix Live Content Analytics Platform** exposes a production-grade FastAPI REST backend delivering real-time catalog analytics, demographic ratings, evidence-based business insights, content search, and automated pipeline execution.

Interactive Swagger UI documentation is available at:
```text
http://localhost:8000/docs
```
Alternative ReDoc documentation is available at:
```text
http://localhost:8000/redoc
```

---

## 1. System Health & Status

### `GET /health`
* **Purpose**: Verifies application availability, database connectivity, and active catalog record counts.
* **Query Parameters**: None.
* **Example Request**:
  ```bash
  curl -X GET http://localhost:8000/health
  ```
* **Example Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "database_record_count": 5834,
    "timestamp": "2026-08-30T07:15:00.123456+00:00",
    "version": "1.0.0"
  }
  ```

---

## 2. Analytics & Reporting Endpoints

All analytics endpoints support multi-criteria query parameters:
* `content_type`: `"Movie"` or `"TV Show"`
* `release_year_min`: Integer (e.g. `2015`)
* `release_year_max`: Integer (e.g. `2020`)
* `country`: Country name substring (e.g. `"India"`, `"United States"`)
* `genre`: Genre name substring (e.g. `"Comedies"`, `"Dramas"`)
* `rating`: Rating code (e.g. `"TV-MA"`, `"PG-13"`)
* `age_group`: Demographic tier (e.g. `"Adults (18+)"`, `"Teens (13-17)"`)

### `GET /api/v1/dashboard/summary`
* **Purpose**: Returns the composite analytics suite in a single payload (overview, format, temporal, geographic, ratings, duration, and insights).
* **Example Request**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/dashboard/summary?content_type=Movie&release_year_min=2018"
  ```
* **Example Response (200 OK)**:
  ```json
  {
    "overview": {
      "total_titles": 2840,
      "movies": 2840,
      "tv_shows": 0,
      "movie_percentage": 100.0,
      "tv_show_percentage": 0.0,
      "total_countries": 94,
      "total_genres": 20
    },
    "content": { ... },
    "temporal": { ... },
    "geographic": { ... },
    "ratings": { ... },
    "duration": { ... },
    "insights": [ ... ]
  }
  ```

### `GET /api/v1/analytics/overview`
* **Purpose**: High-level catalog KPIs including counts, percentages, earliest/latest years, and total unique countries/genres.
* **Example Request**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/analytics/overview"
  ```
* **Example Response (200 OK)**:
  ```json
  {
    "total_titles": 5834,
    "movies": 3937,
    "tv_shows": 1897,
    "movie_percentage": 67.48,
    "tv_show_percentage": 32.52,
    "earliest_release_year": 1925,
    "latest_release_year": 2020,
    "total_countries": 111,
    "total_genres": 42
  }
  ```

### `GET /api/v1/analytics/content`
* **Purpose**: Content format distribution, top genres overall, movie genres, and TV genres.
* **Example Response (200 OK)**:
  ```json
  {
    "content_type": { "labels": ["Movie", "TV Show"], "values": [3937, 1897] },
    "top_genres_overall": { "labels": ["International Movies", "Dramas"], "values": [1795, 1486] },
    "multi_genre_percentage": 52.4
  }
  ```

### `GET /api/v1/analytics/temporal`
* **Purpose**: Ingestion trajectory by year, release year trends, monthly seasonality, and licensing lag statistics.
* **Example Response (200 OK)**:
  ```json
  {
    "yearly_additions": { "years": [2017, 2018, 2019], "counts": [1183, 1629, 1842] },
    "monthly_seasonality": { "months": ["January", "February"], "counts": [580, 420] },
    "licensing_lag_stats": { "median_lag_years": 1.0, "mean_lag_years": 3.8 }
  }
  ```

### `GET /api/v1/analytics/geographic`
* **Purpose**: Top content producing territories and international co-production statistics.
* **Example Response (200 OK)**:
  ```json
  {
    "top_countries_all_credits": { "labels": ["United States", "India"], "values": [2421, 752] },
    "co_production_percentage": 14.5
  }
  ```

### `GET /api/v1/analytics/ratings`
* **Purpose**: Maturity ratings distribution and 5-tier audience demographic classifications.
* **Example Response (200 OK)**:
  ```json
  {
    "dominant_rating": "TV-MA",
    "dominant_age_group": "Adults (18+)",
    "age_groups": { "labels": ["Adults (18+)", "Teens (13-17)"], "values": [2376, 1819] }
  }
  ```

### `GET /api/v1/analytics/duration`
* **Purpose**: Film runtime metrics (mean, median, tiers) and TV series season longevity distributions.
* **Example Response (200 OK)**:
  ```json
  {
    "movies": { "mean_min": 98.01, "median_min": 97.0, "duration_tiers": { ... } },
    "tv_shows": { "mean_seasons": 1.76, "single_season_pct": 66.37 }
  }
  ```

### `GET /api/v1/analytics/insights`
* **Purpose**: Rule-based, observational business insights synthesized from catalog data.
* **Example Response (200 OK)**:
  ```json
  [
    {
      "category": "Catalog Composition",
      "title": "Movie-Heavy Catalog Mix",
      "description": "Movies constitute 67.5% of the total catalog, with TV shows representing 32.5%.",
      "stat": "67.5% Movies / 32.5% TV Shows"
    }
  ]
  ```

---

## 3. Catalog Browsing & Search Endpoints

### `GET /api/v1/content`
* **Purpose**: Paginated catalog exploration with keyword search across `title`, `director`, and `cast`.
* **Query Parameters**:
  - `limit`: Integer, default `50` (1–500)
  - `offset`: Integer, default `0`
  - `search`: Keyword string (e.g. `"Nolan"`, `"Stranger Things"`)
  - Global filters (`content_type`, `year`, `genre`, `country`, `rating`)
* **Example Request**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/content?search=Inception&limit=1"
  ```
* **Example Response (200 OK)**:
  ```json
  {
    "total": 1,
    "limit": 1,
    "offset": 0,
    "data": [
      {
        "show_id": "s341",
        "type": "Movie",
        "title": "Inception",
        "director": "Christopher Nolan",
        "cast": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page",
        "country": "United States, United Kingdom",
        "date_added": "2020-01-01",
        "release_year": 2010,
        "rating": "PG-13",
        "duration": "148 min",
        "listed_in": "Action & Adventure, Sci-Fi & Fantasy, Thrillers",
        "description": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.",
        "duration_min": 148.0,
        "age_group": "Teens (13-17)",
        "primary_country": "United States"
      }
    ]
  }
  ```

### `GET /api/v1/content/{show_id}`
* **Purpose**: Full metadata inspection for a single title by unique identifier.
* **Example Request**:
  ```bash
  curl -X GET http://localhost:8000/api/v1/content/s341
  ```
* **Example Response (200 OK)**: Returns single `ContentItem` object.
* **Error Response (404 Not Found)**:
  ```json
  { "detail": "Content with show_id 's99999' was not found" }
  ```

---

## 4. Ingestion & Pipeline Endpoints

### `GET /api/v1/pipeline/status`
* **Purpose**: Retrieves current database state, record count, and active ingestion configuration.
* **Example Response (200 OK)**:
  ```json
  {
    "status": "ready",
    "database_record_count": 5834,
    "latest_database_update_timestamp": "2026-08-30 06:45:00",
    "configured_data_source_type": "csv",
    "configured_data_source_path": "data/netflix_titles.csv",
    "configured_update_mode": "insert_new_only"
  }
  ```

### `POST /api/v1/pipeline/refresh`
* **Purpose**: Triggers on-demand execution of the automated ETL pipeline with concurrency protection.
* **Request Body**:
  ```json
  {
    "mode": "insert_new_only"
  }
  ```
* **Example Response (200 OK)**:
  ```json
  {
    "success": true,
    "final_status": "SUCCESS",
    "run_id": "pipe_3a8b9c1d",
    "duration_seconds": 1.08,
    "incremental_metrics": {
      "incoming_records": 5837,
      "internal_duplicates": 3,
      "new_records": 0,
      "existing_records": 5834,
      "inserted": 0,
      "updated": 0,
      "skipped": 5834
    }
  }
  ```
* **Conflict Response (409 Conflict)**:
  ```json
  { "detail": "A pipeline execution is already in progress. Please wait for it to finish." }
  ```

### `GET /api/v1/pipeline/history`
* **Purpose**: Retrieves paginated audit ledger of all historical ETL pipeline executions.
* **Query Parameters**:
  - `limit`: Integer, default `20` (1–500)
  - `offset`: Integer, default `0`
  - `status`: Optional filter (`SUCCESS`, `SKIPPED`, `FAILED`, `RUNNING`, `PARTIAL_SUCCESS`)
* **Example Response (200 OK)**:
  ```json
  {
    "total": 14,
    "limit": 20,
    "offset": 0,
    "data": [
      {
        "id": 14,
        "run_id": "pipe_3a8b9c1d",
        "started_at": "2026-08-30T07:10:00+00:00",
        "completed_at": "2026-08-30T07:10:01+00:00",
        "status": "SUCCESS",
        "trigger_type": "MANUAL",
        "update_mode": "insert_new_only",
        "inserted": 0,
        "updated": 0,
        "skipped": 5834,
        "execution_duration": 1.08
      }
    ]
  }
  ```

### `GET /api/v1/pipeline/history/{run_id}`
* **Purpose**: Full execution audit trail including row-level counts and error messages for a specific run.

---

## 5. Automation & Scheduling Endpoints

### `GET /api/v1/automation/status`
* **Purpose**: Live operational status of APScheduler, next scheduled run time, and background execution flags.
* **Example Response (200 OK)**:
  ```json
  {
    "scheduler_enabled": true,
    "scheduler_running": true,
    "update_frequency_seconds": 3600,
    "next_scheduled_run": "2026-08-30T08:00:00+00:00",
    "is_pipeline_running": false,
    "last_pipeline_run": { "run_id": "pipe_3a8b9c1d", "status": "SUCCESS" },
    "last_successful_refresh": { "run_id": "pipe_3a8b9c1d", "completed_at": "..." }
  }
  ```
