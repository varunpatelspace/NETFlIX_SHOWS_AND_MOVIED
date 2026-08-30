"""
APScheduler Background Scheduling Manager for Automated Ingestion.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import (
    ENABLE_SCHEDULER,
    UPDATE_FREQUENCY_SECONDS
)
from database.database import SessionLocal
from automation.jobs import scheduled_refresh_job, is_pipeline_running
from automation.pipeline_monitor import PipelineMonitor

logger = logging.getLogger("PipelineScheduler")

# Global BackgroundScheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or instantiate singleton BackgroundScheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(daemon=True)
    return _scheduler


def start_scheduler() -> bool:
    """
    Start the APScheduler background runner if enabled by configuration.
    
    Returns:
        bool: True if scheduler started or was already running.
    """
    if not ENABLE_SCHEDULER:
        logger.info("APScheduler: Scheduler is disabled via ENABLE_SCHEDULER=false.")
        return False

    sched = get_scheduler()
    if sched.running:
        logger.info("APScheduler: Scheduler is already running.")
        return True

    # Register the automated refresh job
    sched.add_job(
        func=scheduled_refresh_job,
        trigger=IntervalTrigger(seconds=UPDATE_FREQUENCY_SECONDS),
        id="netflix_catalog_refresh",
        name="Automated Netflix Catalog Change Detection & Ingestion",
        replace_existing=True,
        max_instances=1
    )

    sched.start()
    logger.info(f"APScheduler: Background scheduler started. Interval: {UPDATE_FREQUENCY_SECONDS}s.")
    return True


def stop_scheduler():
    """Gracefully shutdown the APScheduler background runner."""
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.info("APScheduler: Shutting down background scheduler...")
        _scheduler.shutdown(wait=False)
        _scheduler = None


def get_scheduler_status(db: Optional[Any] = None) -> Dict[str, Any]:
    """
    Retrieve live operational state of the scheduler and background job execution.
    """
    sched = _scheduler
    is_running = sched.running if sched else False
    next_run = None

    if is_running and sched:
        job = sched.get_job("netflix_catalog_refresh")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()

    # Query latest pipeline run and success run from DB
    owns_session = db is None
    session = db or SessionLocal()
    last_run_dict = None
    last_success_dict = None
    try:
        last_run = PipelineMonitor.get_last_run(session)
        if last_run:
            last_run_dict = last_run.to_dict()

        last_success = PipelineMonitor.get_last_successful_run(session)
        if last_success:
            last_success_dict = last_success.to_dict()
    except Exception as e:
        logger.debug(f"Could not retrieve pipeline status from DB: {e}")
    finally:
        if owns_session:
            session.close()

    return {
        "scheduler_enabled": ENABLE_SCHEDULER,
        "scheduler_running": is_running,
        "update_frequency_seconds": UPDATE_FREQUENCY_SECONDS,
        "next_scheduled_run": next_run,
        "is_pipeline_running": is_pipeline_running(),
        "last_pipeline_run": last_run_dict,
        "last_successful_refresh": last_success_dict
    }
