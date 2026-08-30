# Local Installation & Developer Setup Guide

This guide provides step-by-step instructions to clone, configure, initialize, and execute the **Netflix Live Content Analytics Platform** in a local Python environment.

---

## 1. Prerequisites

Before installing, ensure your environment meets the following requirements:
* **Python**: Version `3.10`, `3.11`, or `3.12+` (`python --version`)
* **Package Manager**: `pip` (v22.0+)
* **Version Control**: `git` (v2.30+)
* **OS**: Compatible with Windows 10/11, macOS (Intel/Apple Silicon), and Linux (Ubuntu, Debian, Fedora)
* **Optional**: Docker & Docker Compose (if container deployment is preferred)

---

## 2. Step-by-Step Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/netflix-live-analytics.git
cd netflix-live-analytics
```

### Step 2: Create & Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell / CMD):
venv\Scripts\activate

# Activate on macOS / Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy the configuration template:
```bash
# On Windows:
copy .env.example .env

# On macOS / Linux:
cp .env.example .env
```
Default settings work out-of-the-box with local SQLite (`data/netflix_live.db`).

---

## 3. Database Initialization & Initial Ingestion

### Step 1: Initialize Database Tables
```bash
python -c "from database.database import init_db; init_db(); print('Tables created successfully!')"
```

### Step 2: Run Baseline ETL Ingestion
Ingest the 5,837-row catalog into the SQLite database:
```bash
python -c "from pipeline.pipeline_runner import run_pipeline; report = run_pipeline(); print(f'Pipeline completed: {report[\"final_status\"]}')"
```

---

## 4. Running the Platform Locally

Run the backend and frontend in two separate terminal windows:

### Terminal 1: Launch FastAPI REST Backend
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Home**: `http://127.0.0.1:8000`
* **Swagger Docs**: `http://127.0.0.1:8000/docs`
* **Health Check**: `http://127.0.0.1:8000/health`

### Terminal 2: Launch Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
* **Web UI**: `http://localhost:8501`

---

## 5. Verification & Testing

### Run Automated Unit Test Suite
Execute all 50 unit tests across 7 test suites:
```bash
python -m pytest tests/ -v
```

### Verify Legacy Exploratory Analysis
Verify that static charts and markdown business reports continue to build cleanly:
```bash
python run_analysis.py
```

### Run Demonstration Scenarios
To run the automated change detection and audit ledger demonstration:
```bash
python demo_phase8_automation.py
```
