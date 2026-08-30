"""
Data Extraction Module for Netflix Live Content Analytics Platform.

Extracts raw Netflix catalog data from the configured data source
using the Data Source Factory. Captures extraction metadata without
performing any data cleaning or transformation.
"""

import logging
from datetime import datetime, timezone
from typing import Tuple, Dict, Any, Optional
import pandas as pd

from pipeline.data_sources.factory import get_data_source
from pipeline.data_sources.base_source import BaseDataSource

logger = logging.getLogger(__name__)


def extract_raw_data(
    source_type: Optional[str] = None,
    source_path: Optional[str] = None,
    **source_kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Extract raw catalog data from the configured data source.
    
    Args:
        source_type: 'csv' or 'api'. Defaults to configured DATA_SOURCE_TYPE.
        source_path: File path or endpoint URL. Defaults to DATA_SOURCE_PATH.
        **source_kwargs: Additional arguments for the data source.
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: 
            - raw_df: Unmodified raw dataset.
            - extraction_metadata: Operational details (timestamp, source info, row count).
            
    Raises:
        FileNotFoundError: If source file is missing.
        ValueError: If source is invalid or empty.
        Exception: On connection or read failures.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting Data Extraction stage...")

    # 1. Instantiate configured data source via factory
    data_source: BaseDataSource = get_data_source(
        source_type=source_type,
        source_path=source_path,
        **source_kwargs
    )

    # 2. Validate accessibility of source
    data_source.validate_source()

    # 3. Extract raw data without modification
    raw_df = data_source.fetch_raw_data()
    end_time = datetime.now(timezone.utc)

    extraction_metadata = {
        "source_name": data_source.name,
        "source_type": data_source.source_type,
        "source_location": data_source.location,
        "extraction_started_at": start_time.isoformat(),
        "extraction_completed_at": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 4),
        "raw_record_count": len(raw_df),
        "raw_columns": list(raw_df.columns),
        "status": "extracted"
    }

    logger.info(
        f"Data Extraction successful: {len(raw_df):,} raw records retrieved "
        f"from '{data_source.name}' in {extraction_metadata['duration_seconds']}s."
    )

    return raw_df, extraction_metadata
