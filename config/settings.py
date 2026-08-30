"""
Centralized Configuration Settings for Netflix Live Content Analytics Platform.

Supports environment variable overrides for multi-environment deployments
(local SQLite, Docker, PostgreSQL staging/production).
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure essential directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration (SQLite default with PostgreSQL compatibility)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{DATA_DIR / 'netflix_live.db'}"
)

# Data Ingestion & Incremental Update Configuration
DATA_SOURCE_TYPE = os.getenv("DATA_SOURCE_TYPE", "csv").lower()
DATA_SOURCE_PATH = os.getenv("DATA_SOURCE_PATH", str(DATA_DIR / "netflix_titles.csv"))
DATA_UPDATE_MODE = os.getenv("DATA_UPDATE_MODE", "insert_new_only").lower()  # 'insert_new_only' or 'upsert'
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{API_HOST}:{API_PORT}")

# CORS Configuration (comma-separated origins or '*' for public access)
ALLOWED_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000"
)
CORS_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

# Database Auto-Seeding (seeds empty database on fresh cloud container deployment)
AUTO_SEED_DB = os.getenv("AUTO_SEED_DB", "true").lower() in ("true", "1", "yes")

# Dashboard Configuration
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
DASHBOARD_PORT = int(os.getenv("PORT", os.getenv("DASHBOARD_PORT", "8501")))

# Automation & Scheduler Configuration
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").lower() in ("true", "1", "yes")
UPDATE_FREQUENCY_SECONDS = int(os.getenv("UPDATE_FREQUENCY_SECONDS", "3600"))
AUTO_REFRESH_ENABLED = os.getenv("AUTO_REFRESH_ENABLED", "true").lower() in ("true", "1", "yes")
SOURCE_CHANGE_DETECTION = os.getenv("SOURCE_CHANGE_DETECTION", "true").lower() in ("true", "1", "yes")
UPDATE_FREQUENCY = os.getenv("UPDATE_FREQUENCY", "MANUAL").upper()

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = LOGS_DIR / "platform.log"

