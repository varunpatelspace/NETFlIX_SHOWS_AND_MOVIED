# Docker & Docker Compose Production Deployment Guide

This guide details the containerized deployment of the **Netflix Live Content Analytics Platform**, explaining image builds, service orchestration, persistence guarantees, and maintenance workflows.

---

## 1. Container Architecture

The platform runs as two containerized microservices managed by **Docker Compose**:
1. **`api` Service (`netflix_analytics_api`)**:
   - Runs FastAPI via Uvicorn ASGI on port `8000`.
   - Mounts persistent volumes: `netflix_data` (`/app/data`) and `netflix_logs` (`/app/logs`).
   - Runs APScheduler in the background for automated change detection.
   - Verified via Docker native healthchecks (`GET /health`).
2. **`dashboard` Service (`netflix_analytics_dashboard`)**:
   - Runs Streamlit UI on port `8501`.
   - Communicates with the backend using internal bridge DNS: `http://api:8000`.
   - Starts only after the `api` service reports healthy (`depends_on.api.condition: service_healthy`).

---

## 2. Quick Start

### Step 1: Build & Launch
Build the Docker images and launch both services in the foreground:
```bash
docker compose up --build
```

### Step 2: Run in Detached Mode (Background)
To run the containers in the background as daemon processes:
```bash
docker compose up -d --build
```

---

## 3. Service Access Endpoints

Once initialized, services are accessible on your host machine:

| Component | Host URL | Description |
| :--- | :--- | :--- |
| **Streamlit UI** | [`http://localhost:8501`](http://localhost:8501) | Interactive Netflix Dark Analytics Dashboard |
| **FastAPI REST API** | [`http://localhost:8000`](http://localhost:8000) | Live data ingestion & metrics REST API |
| **Interactive Docs** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Swagger UI for interactive API exploration |
| **Alternative Docs** | [`http://localhost:8000/redoc`](http://localhost:8000/redoc) | ReDoc API specification viewer |
| **Health Endpoint** | [`http://localhost:8000/health`](http://localhost:8000/health) | Container health & database probe |

---

## 4. Monitoring & Container Operations

### Inspect Service Status
Check container state, uptime, and healthcheck status:
```bash
docker compose ps
```
*Expected Output*: Both `netflix_analytics_api` and `netflix_analytics_dashboard` reporting `Up` and `(healthy)`.

### Stream Live Logs
Follow streaming logs from both services:
```bash
# Stream combined logs
docker compose logs -f

# Stream specific service
docker compose logs -f api
docker compose logs -f dashboard
```

---

## 5. Storage Persistence & Shutdown Lifecycle

### Stopping Containers (Preserving Data)
To halt container execution without losing ingested catalog data, audit logs, or fingerprints:
```bash
docker compose down
```
> **What Happens**: Containers are stopped and removed, but named Docker volumes (`netflix_data` and `netflix_logs`) remain intact on disk. When you run `docker compose up` again, the database state is completely preserved.

### Stopping & Wiping Database (Complete Reset)
To stop containers and permanently purge persistent database and log volumes:
```bash
docker compose down -v
```
> **What Happens**: Destroys the containers *and deletes* `netflix_data` and `netflix_logs`. The next launch will rebuild fresh storage and run initial database initialization from scratch.

---

## 6. Production Hardening Checklist
* [x] **Slim Base Images**: Built on `python:3.11-slim` with zero compiler toolchain bloat.
* [x] **No Root Secrets**: Sensitive keys supplied strictly through environment variables.
* [x] **Healthchecks**: Automated probes periodically test socket and database connectivity.
* [x] **Restart Policies**: Configured with `restart: unless-stopped` for self-healing.
* [x] **Volume Isolation**: Data directory separated from container ephemeral layers.
