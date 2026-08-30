# Portfolio Project Descriptions: Netflix Live Content Analytics Platform

This document provides tailored project descriptions for resumes, LinkedIn profiles, personal portfolios, and engineering presentations.

---

## 1. Short Version (Resume / Bullet Points)

**Netflix Live Content Analytics Platform | Full-Stack Data & Analytics Platform**
* Architected an automated, production-grade analytics platform using Python, FastAPI, Streamlit, and SQLAlchemy to ingest, clean, and analyze 5,800+ global entertainment titles.
* Engineered a 6-stage idempotent ETL pipeline featuring two-tier deduplication, SHA-256 source change detection, and automated background sync via APScheduler.
* Containerized multi-service deployment with Docker Compose, featuring persistent SQLite storage, sub-15ms REST API query endpoints, and interactive Netflix-styled Plotly analytics.

---

## 2. Medium Version (LinkedIn / Summary Showcase)

### Netflix Live Content Analytics Platform
**Transforming Static Dataset Analysis into an Automated, Monitored Data Platform**

Most data science portfolio projects rely on static Jupyter Notebooks that break as soon as source data updates. I designed and implemented the **Netflix Live Content Analytics Platform** to bridge the gap between static exploratory data analysis and production-ready data engineering.

**Core Highlights:**
- **Automated Data Engineering**: Built a 6-stage idempotent ETL pipeline (Extract, Validate, Clean, Feature Engineer, Deduplicate, Load) with two-tier collision handling and transactional rollback safety.
- **Change Detection & Scheduling**: Implemented background automation using APScheduler with cryptographic SHA-256 fingerprinting to eliminate redundant ETL runs.
- **RESTful Analytics API**: Developed a decoupled FastAPI backend with Pydantic validation, dynamic filtering, full-text search, and automated OpenAPI documentation.
- **Executive BI Dashboard**: Built an interactive, dark-themed Streamlit frontend consuming backend APIs with Plotly visualizations, catalog drill-down, and live audit logging.
- **Production Containerization**: Deployed via Docker Compose with persistent database volumes, health checks, and structured logging.

**Tech Stack**: Python, FastAPI, Streamlit, SQLAlchemy, SQLite, APScheduler, Plotly, Pandas, Docker, Docker Compose, Pytest (50 automated tests).

---

## 3. Technical Version (Portfolio Website / GitHub Profile)

### Project Overview: Netflix Live Content Analytics Platform

#### The Problem
Data analytics codebases frequently suffer from "notebook stagnation"—where data cleaning, exploratory statistics, and visual charts remain trapped inside one-off scripts. In real-world enterprise environments, datasets evolve constantly, requiring automated ingestion, schema validation, deduplication, persistent relational storage, and API-driven delivery.

#### The Solution
The **Netflix Live Content Analytics Platform** is a full-stack, automated data engineering and analytics system built around a 5,830+ title catalog. It unifies modular ETL data engineering, relational database persistence, parameterized analytics, RESTful API services, and interactive web visualization into a cohesive, containerized application.

#### System Architecture & Engineering Challenges
1. **Idempotent 6-Stage Ingestion Pipeline**:
   - Built a modular pipeline (`Extract -> Validate -> Clean -> Transform -> Deduplicate -> Load`).
   - Implemented fatal schema validation alongside non-fatal row-level anomaly quarantine.
   - Solved data collision issues via two-tier deduplication: **Level A** removes in-batch duplicates across `title + type + release_year`, while **Level B** queries existing database IDs to distinguish genuinely new titles from pre-existing records.
2. **Conditional Automation & Concurrency**:
   - Integrated `APScheduler` for autonomous background data synchronization.
   - Designed a `SourceMonitor` that computes streaming SHA-256 checksums, file sizes, and row counts. If an incoming file has not changed, the pipeline logs a `SKIPPED` audit entry and terminates before running expensive operations.
   - Implemented thread-level process locking to prevent concurrent manual and scheduled ingestion conflicts.
3. **Decoupled API & Presentation Architecture**:
   - The FastAPI backend exposes RESTful endpoints with sub-15ms response times, Pydantic type validation, and multi-criteria query parameters.
   - The Streamlit frontend is decoupled, interacting strictly over HTTP via a custom `ApiClient` with fallback error states, ensuring frontend sessions never hold database file locks.
4. **Reliable Containerized Deployment**:
   - Multi-service Docker Compose architecture with persistent named volumes (`netflix_data`, `netflix_logs`).
   - Docker native health checks (`GET /health`) ensure proper container startup ordering and self-healing.

#### Verified Quality & Reliability
- **50 Automated Unit Tests**: Complete test coverage across database operations, pipeline validation, idempotency, incremental updates, REST API contracts, and background scheduling.
- **100% Backward Compatibility**: Legacy exploratory data analysis (`run_analysis.py`) remains fully operational, generating 12 publication-grade figures in under 7 seconds.
