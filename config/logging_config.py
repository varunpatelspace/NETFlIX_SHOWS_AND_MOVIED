"""
Structured Production Logging Configuration for Netflix Live Content Analytics Platform.

Configures formatted console and dedicated file logging:
  - logs/application.log : Root application, FastAPI, and general events
  - logs/pipeline.log    : ETL execution, extraction, deduplication, and loading
  - logs/scheduler.log   : APScheduler, background execution, and change detection
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from config.settings import LOGS_DIR, LOG_LEVEL

_logging_configured = False


def setup_logging(level: Optional[str] = None) -> None:
    """
    Initialize structured logging with dedicated file handlers.
    Thread-safe and idempotent.
    """
    global _logging_configured
    if _logging_configured:
        return

    log_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # 1. Root / Console Handler
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate stream handlers
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 2. logs/application.log Handler (Catches all app logs)
    app_log_file = LOGS_DIR / "application.log"
    app_handler = logging.FileHandler(app_log_file, encoding="utf-8")
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)
    root_logger.addHandler(app_handler)

    # 3. logs/pipeline.log Handler (ETL specific loggers)
    pipe_log_file = LOGS_DIR / "pipeline.log"
    pipe_handler = logging.FileHandler(pipe_log_file, encoding="utf-8")
    pipe_handler.setLevel(log_level)
    pipe_handler.setFormatter(formatter)

    for p_logger_name in ["pipeline", "PipelineRunner", "pipeline.fetch_data", "pipeline.clean_data", "pipeline.deduplicate", "pipeline.load_data"]:
        p_logger = logging.getLogger(p_logger_name)
        p_logger.addHandler(pipe_handler)

    # 4. logs/scheduler.log Handler (Scheduler and Automation specific loggers)
    sched_log_file = LOGS_DIR / "scheduler.log"
    sched_handler = logging.FileHandler(sched_log_file, encoding="utf-8")
    sched_handler.setLevel(log_level)
    sched_handler.setFormatter(formatter)

    for s_logger_name in ["PipelineScheduler", "PipelineAutomation", "automation"]:
        s_logger = logging.getLogger(s_logger_name)
        s_logger.addHandler(sched_handler)

    _logging_configured = True
    logging.getLogger("NetflixPlatform").info("Structured production logging initialized.")
