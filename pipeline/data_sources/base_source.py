"""
Abstract Base Data Source Interface for Netflix Live Content Analytics Platform.

Defines the contract that every data source provider (CSV, REST API, Cloud Stream)
must implement. Ensures raw data ingestion is completely decoupled from cleaning,
transformation, persistence, and presentation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class BaseDataSource(ABC):
    """
    Abstract Base Class for all ingestion data sources.
    
    Responsibilities:
    - Validate connectivity / existence of the data source.
    - Fetch raw data without modifying or cleaning it.
    - Track metadata (source identifier, fetch timestamp, record count).
    """

    def __init__(self, name: str, source_type: str, location: str):
        self.name = name
        self.source_type = source_type
        self.location = location
        self.last_fetched_at: Optional[str] = None
        self.record_count: Optional[int] = None
        self.columns: Optional[list] = None
        self.status: str = "initialized"

    @abstractmethod
    def validate_source(self) -> bool:
        """
        Verify that the configured data source exists, is accessible,
        and provides readable data.
        
        Returns:
            bool: True if source is healthy and accessible, False otherwise.
        """
        pass

    @abstractmethod
    def fetch_raw_data(self) -> pd.DataFrame:
        """
        Retrieve raw records from the data source as a Pandas DataFrame.
        
        CRITICAL: This method MUST NOT clean, transform, or impute data.
        It strictly handles raw extraction.
        
        Returns:
            pd.DataFrame: Unmodified raw dataset.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Retrieve operational metadata regarding the last fetch operation.
        
        Returns:
            dict: Source details, location, status, record count, and timestamp.
        """
        return {
            "name": self.name,
            "source_type": self.source_type,
            "location": self.location,
            "status": self.status,
            "last_fetched_at": self.last_fetched_at,
            "record_count": self.record_count,
            "columns": self.columns,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.source_type}', location='{self.location}')>"
