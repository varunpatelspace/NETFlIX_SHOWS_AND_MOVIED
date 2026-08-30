"""
Pipeline and ingestion status schemas for Netflix Live Content Analytics Platform.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health check response."""
    status: str
    database: str
    database_record_count: int
    timestamp: str
    version: str = "1.0.0"


class PipelineRefreshRequest(BaseModel):
    """Payload to trigger ETL pipeline refresh."""
    mode: Optional[str] = Field(
        default="insert_new_only",
        description="Ingestion update mode: 'insert_new_only' or 'upsert'"
    )
    source_type: Optional[str] = Field(
        default=None,
        description="Optional source override ('csv' or 'api')"
    )
    source_path: Optional[str] = Field(
        default=None,
        description="Optional path or endpoint URL override"
    )


class PipelineStatusResponse(BaseModel):
    """System ingestion configuration and current database state."""
    status: str
    database_record_count: int
    latest_database_update_timestamp: Optional[str]
    configured_data_source_type: str
    configured_data_source_path: str
    configured_update_mode: str
    historical_pipeline_records: str = "Current system status only"
