"""
Main FastAPI Application Entrypoint for Netflix Live Content Analytics Platform.
"""

import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from contextlib import asynccontextmanager
from config.settings import API_HOST, API_PORT
from database.database import init_db
from automation.scheduler import start_scheduler, stop_scheduler
from config.logging_config import setup_logging
from pipeline.validate_data import DataValidationError
from api.routes import health_router, analytics_router, content_router, pipeline_router

# Initialize structured logging
setup_logging()
logger = logging.getLogger("NetflixAPI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and graceful shutdown tasks."""
    logger.info("FastAPI Startup: Initializing structured logging and database tables...")
    init_db()
    logger.info("FastAPI Startup: Checking background scheduler...")
    start_scheduler()
    yield
    logger.info("FastAPI Shutdown: Gracefully stopping background scheduler...")
    stop_scheduler()
    logger.info("FastAPI Shutdown: Application teardown complete.")


# Initialize FastAPI Application
app = FastAPI(
    title="Netflix Live Content Analytics API",
    description=(
        "Production-grade RESTful API delivering real-time catalog analytics, "
        "evidence-based business insights, content search & pagination, "
        "and automated incremental data ingestion for the Netflix Live Content Analytics Platform."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware for modern frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle structured HTTP exceptions."""
    error_code = "HTTP_ERROR"
    if exc.status_code == 404:
        error_code = "CONTENT_NOT_FOUND"
    elif exc.status_code == 400:
        error_code = "BAD_REQUEST"
    elif exc.status_code == 503:
        error_code = "SERVICE_UNAVAILABLE"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": error_code
        }
    )


@app.exception_handler(DataValidationError)
async def data_validation_exception_handler(request: Request, exc: DataValidationError):
    """Handle pipeline schema validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "error_code": "DATA_VALIDATION_ERROR"
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic schema validation failures."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "error_code": "SCHEMA_VALIDATION_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler that protects against stack trace leakage."""
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing your request.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )


# Register Application Routers
app.include_router(health_router)
app.include_router(analytics_router)
app.include_router(content_router)
app.include_router(pipeline_router)


if __name__ == "__main__":
    import uvicorn
    print(f"\nStarting Netflix Live Content Analytics API at http://{API_HOST}:{API_PORT}...")
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)
