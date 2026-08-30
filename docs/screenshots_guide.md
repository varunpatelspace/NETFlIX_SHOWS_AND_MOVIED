# Visual Assets & Screenshot Capturing Guide

This document defines the standard catalog of visual assets and screenshots recommended for repository showcasing, conference slides, and portfolio presentations.

Screenshots should be saved under:
```text
docs/images/
```

---

## 1. Recommended Visual Asset Checklist

| # | Asset Identifier | Target URL / View | Recommended Capture Elements |
| :- | :--- | :--- | :--- |
| 1 | `01_dashboard_home.png` | `http://localhost:8501` | Executive Overview with 5 KPI cards, Movie vs TV donut chart, and content additions line chart. |
| 2 | `02_filtered_analytics.png` | `http://localhost:8501/2_Content_Analysis` | Content analysis page showing multi-genre share and movie vs TV genre comparison bars. |
| 3 | `03_temporal_trends.png` | `http://localhost:8501/3_Temporal_Trends` | Yearly additions, release trends, and monthly seasonality bar charts. |
| 4 | `04_geographic_footprint.png` | `http://localhost:8501/4_Geographic_Analysis` | Interactive Plotly choropleth world map and top 12 producing countries. |
| 5 | `05_ratings_demographics.png` | `http://localhost:8501/5_Ratings_and_Audience` | 5-tier audience demographic breakdown and rating cross-tabulation. |
| 6 | `06_content_explorer.png` | `http://localhost:8501/7_Content_Explorer` | Keyword search interface with paginated table and expanded title detail card. |
| 7 | `07_data_management.png` | `http://localhost:8501/8_Data_Management` | Scheduler status, live SHA-256 fingerprint card, and on-demand refresh trigger. |
| 8 | `08_pipeline_history.png` | `http://localhost:8501/8_Data_Management` | Audit history table displaying `SUCCESS`, `SKIPPED`, and `FAILED` status badges. |
| 9 | `09_swagger_api_docs.png` | `http://localhost:8000/docs` | FastAPI Swagger interactive OpenAPI interface showing categorized endpoints. |
| 10 | `10_docker_compose_ps.png` | Terminal | Terminal showing `docker compose ps` with both `api` and `dashboard` healthy. |

---

## 2. Screenshot Capture Procedure

Follow these instructions to capture crisp, high-resolution visual assets:

### Step 1: Launch Local Services
In two terminal windows, start the API and dashboard:
```bash
# Terminal 1:
uvicorn api.main:app --host 127.0.0.1 --port 8000

# Terminal 2:
streamlit run dashboard/app.py
```

### Step 2: Configure Browser Resolution
1. Open Chrome, Firefox, or Edge.
2. Set browser zoom level to **100%**.
3. Set your viewport resolution to **1920 x 1080** (Full HD) or maximize window.

### Step 3: Capture & Save
1. Navigate to the target page URL listed in the table above.
2. Use your operating system capture tool:
   - **Windows**: `Win + Shift + S`
   - **macOS**: `Cmd + Shift + 4`
   - **Linux**: `gnome-screenshot -a`
3. Save each image as a clean PNG file in `docs/images/` using the exact identifier filenames listed above (e.g. `docs/images/01_dashboard_home.png`).

---

## 3. Formatting Guidelines for Markdown Embedding
When adding captured screenshots to `README.md` or presentation documents, use standard Markdown image tags with descriptive alt captions:
```markdown
![Dashboard Executive Overview](docs/images/01_dashboard_home.png)
```
*(Note: Do not check in temporary or placeholder images until authentic full-resolution captures are recorded).*
