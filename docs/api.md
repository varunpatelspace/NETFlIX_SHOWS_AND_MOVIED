# Netflix Live Content Analytics API Reference

The **Netflix Live Content Analytics API** is a high-performance RESTful service built with FastAPI that exposes real-time catalog analytics, deterministic business insights, multi-criteria content search with pagination, and on-demand ETL ingestion triggers.

---

## Server Execution

Start the development server using Uvicorn:
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive Documentation URLs:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## Standard Filter Parameters

The analytics and content browsing endpoints support centralized query parameters:

| Parameter | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `content_type` | string | `Movie` or `TV Show` | Filter by content format |
| `release_year_min` | integer | `2015` | Minimum release year bound |
| `release_year_max` | integer | `2020` | Maximum release year bound |
| `country` | string | `United States` | Producing country substring match |
| `genre` | string | `Dramas` | Genre classification substring match |
| `rating` | string | `TV-MA` | Maturity certification code |
| `age_group` | string | `Adults (18+)` | Standardized demographic tier |

---

## Endpoint Catalog

### 1. System Health
#### `GET /health`
Verifies API availability and live database connectivity.

**Response `(200 OK)`**:
```json
{
  "status": "healthy",
  "database": "connected",
  "database_record_count": 5834,
  "timestamp": "2026-08-30T06:30:00.000000Z",
  "version": "1.0.0"
}
```

---

### 2. Dashboard Summary
#### `GET /api/v1/dashboard/summary`
Returns the consolidated analytics suite (overview, content, temporal, geographic, ratings, duration, and insights) in a single request.

**Example Request**:
```http
GET /api/v1/dashboard/summary?content_type=Movie&release_year_min=2018
```

---

### 3. Domain Analytics Endpoints

#### `GET /api/v1/analytics/overview`
Catalog KPIs including title totals, format ratios, release year spans, and database freshness.

**Response `(200 OK)`**:
```json
{
  "total_titles": 5834,
  "movies": 3937,
  "tv_shows": 1897,
  "movie_percentage": 67.48,
  "tv_show_percentage": 32.52,
  "earliest_release_year": 1925,
  "latest_release_year": 2020,
  "average_release_year": 2013.7,
  "total_countries": 71,
  "total_genres": 42,
  "database_freshness": "2026-08-30T06:09:24"
}
```

#### `GET /api/v1/analytics/content`
Content format splits, top genres overall, movie genres, and TV genres.

#### `GET /api/v1/analytics/temporal`
Yearly addition volume, release year trends, monthly seasonality, and licensing lag.

#### `GET /api/v1/analytics/geographic`
Top producing territories, primary country hubs, and international co-production percentage.

#### `GET /api/v1/analytics/ratings`
Certification ratings breakdown and 5-tier demographic classifications.

#### `GET /api/v1/analytics/duration`
Movie runtime distributions/tiers and TV show seasons longevity metrics.

#### `GET /api/v1/analytics/insights`
Evidence-based, deterministic business observations generated from calculated metrics.

**Response `(200 OK)`**:
```json
[
  {
    "category": "content_mix",
    "title": "Movie Catalog Dominance",
    "description": "Movies account for 67.48% (3,937 titles) of the catalog compared to 32.52% TV shows (1,897 titles). Feature film content represents the primary catalog format.",
    "stat": "67.48% Movies"
  },
  {
    "category": "geographic_dominance",
    "title": "Top Producing Territory: United States",
    "description": "United States leads all international producing territories, appearing in 41.5% of total title credits. Furthermore, 14.5% of catalog titles involve cross-border co-productions.",
    "stat": "41.5% (United States)"
  }
]
```

---

### 4. Content Browsing & Details

#### `GET /api/v1/content`
Paginated browsing of catalog titles.

**Query Parameters**:
- `limit` (default: 50, max: 500)
- `offset` (default: 0)
- Any standard filter parameters

**Response `(200 OK)`**:
```json
{
  "total": 5834,
  "limit": 2,
  "offset": 0,
  "data": [
    {
      "show_id": "s1",
      "type": "Movie",
      "title": "Dick Johnson Is Dead",
      "director": "Kirsten Johnson",
      "release_year": 2020,
      "rating": "PG-13",
      "duration": "90 min",
      "duration_min": 90.0,
      "primary_country": "United States",
      "listed_in": "Documentaries",
      "age_group": "Teens (13-17)"
    }
  ]
}
```

#### `GET /api/v1/content/{show_id}`
Retrieve a single title by unique primary key.

**Response `(200 OK)`**: Title detail JSON object.

**Error Response `(404 Not Found)`**:
```json
{
  "detail": "Content with show_id 'nonexistent_id' was not found",
  "error_code": "CONTENT_NOT_FOUND"
}
```

---

### 5. Pipeline Ingestion & Control

#### `GET /api/v1/pipeline/status`
Returns database record counts, freshness timestamp, and active ingestion settings.

**Response `(200 OK)`**:
```json
{
  "status": "ready",
  "database_record_count": 5834,
  "latest_database_update_timestamp": "2026-08-30T06:09:24",
  "configured_data_source_type": "csv",
  "configured_data_source_path": "data/netflix_titles.csv",
  "configured_update_mode": "insert_new_only",
  "historical_pipeline_records": "Current system status only"
}
```

#### `POST /api/v1/pipeline/refresh`
Triggers on-demand execution of the automated ETL pipeline.

**Request Body**:
```json
{
  "mode": "insert_new_only"
}
```

**Response `(200 OK)`**:
Full pipeline execution audit report detailing stage metrics and database persistence counts.
