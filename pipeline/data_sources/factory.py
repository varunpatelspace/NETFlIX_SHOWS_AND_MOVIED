"""
Data Source Factory for dynamic provider instantiation based on environment configuration.
"""

import logging
from typing import Optional
from config.settings import DATA_SOURCE_TYPE, DATA_SOURCE_PATH
from pipeline.data_sources.base_source import BaseDataSource
from pipeline.data_sources.csv_source import CSVDataSource
from pipeline.data_sources.api_source import APIDataSource

logger = logging.getLogger(__name__)


def get_data_source(
    source_type: Optional[str] = None,
    source_path: Optional[str] = None,
    **kwargs
) -> BaseDataSource:
    """
    Factory function to instantiate the configured data source.
    
    Args:
        source_type: 'csv' or 'api'. Defaults to settings.DATA_SOURCE_TYPE.
        source_path: Path or URL for the data source.
        **kwargs: Additional parameters passed to the data source constructor.
        
    Returns:
        BaseDataSource: An instantiated data source instance.
        
    Raises:
        ValueError: If an unsupported source_type is requested.
    """
    stype = (source_type or DATA_SOURCE_TYPE).lower().strip()

    if stype == "csv":
        target_path = source_path or DATA_SOURCE_PATH
        logger.info(f"Instantiating CSVDataSource with path: '{target_path}'")
        return CSVDataSource(file_path=target_path, **kwargs)

    elif stype == "api":
        logger.info("Instantiating APIDataSource skeleton.")
        return APIDataSource(endpoint_url=source_path, **kwargs)

    else:
        supported = ["csv", "api"]
        raise ValueError(
            f"Unsupported DATA_SOURCE_TYPE: '{stype}'. Supported options: {supported}"
        )
