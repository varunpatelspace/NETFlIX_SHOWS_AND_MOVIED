"""
CSV Data Source Implementation for Netflix Live Content Analytics Platform.

Reads raw Netflix catalog datasets from local or mounted CSV files.
Provides source validation, metadata tracking, and raw data extraction.
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
import pandas as pd

from config.settings import DATA_SOURCE_PATH
from pipeline.data_sources.base_source import BaseDataSource

logger = logging.getLogger(__name__)


class CSVDataSource(BaseDataSource):
    """
    Data source for reading raw Netflix catalog data from CSV files.
    """

    def __init__(
        self,
        file_path: Optional[str] = None,
        name: str = "Netflix_CSV_Primary",
        encoding: str = "utf-8"
    ):
        target_path = file_path or DATA_SOURCE_PATH
        self.file_path = self._resolve_path(target_path)
        self.encoding = encoding

        super().__init__(
            name=name,
            source_type="csv",
            location=str(self.file_path)
        )

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve path to an absolute Path, checking relative to cwd or repo base."""
        p = Path(path_str)
        if p.is_absolute() and p.exists():
            return p
        if p.exists():
            return p.resolve()
        
        # Check relative to project root
        repo_base = Path(__file__).resolve().parent.parent.parent
        alt = repo_base / path_str
        if alt.exists():
            return alt.resolve()

        return p.resolve()

    def validate_source(self) -> bool:
        """
        Validate that the configured CSV file exists, is readable, and contains data.
        
        Returns:
            bool: True if file exists, is non-empty, and can be read.
            
        Raises:
            FileNotFoundError: If the CSV file does not exist.
            ValueError: If the file is empty or corrupted.
        """
        if not self.file_path.exists():
            self.status = "error_not_found"
            msg = f"CSV data source file not found at: '{self.file_path}'"
            logger.error(msg)
            raise FileNotFoundError(msg)

        if not self.file_path.is_file():
            self.status = "error_invalid_path"
            msg = f"Path '{self.file_path}' is a directory, not a CSV file."
            logger.error(msg)
            raise ValueError(msg)

        if self.file_path.stat().st_size == 0:
            self.status = "error_empty_file"
            msg = f"CSV data source file is empty (0 bytes): '{self.file_path}'"
            logger.error(msg)
            raise ValueError(msg)

        try:
            # Read first row to test readability and header presence
            preview_df = pd.read_csv(self.file_path, nrows=1, encoding=self.encoding)
            if preview_df.shape[1] == 0:
                self.status = "error_no_columns"
                raise ValueError(f"CSV file '{self.file_path}' contains no columns.")
            
            self.status = "validated"
            return True
        except Exception as e:
            self.status = "error_read_failure"
            logger.error(f"Failed to read CSV header from '{self.file_path}': {e}")
            raise

    def fetch_raw_data(self) -> pd.DataFrame:
        """
        Load the raw CSV file into a Pandas DataFrame.
        
        Returns:
            pd.DataFrame: Unmodified raw data.
        """
        self.validate_source()

        logger.info(f"Extracting raw data from CSV source: '{self.file_path}'")
        df = pd.read_csv(self.file_path, encoding=self.encoding)

        # Update metadata
        self.last_fetched_at = datetime.now(timezone.utc).isoformat()
        self.record_count = len(df)
        self.columns = list(df.columns)
        self.status = "fetched"

        logger.info(
            f"Successfully fetched {self.record_count:,} raw records "
            f"with {len(self.columns)} columns from '{self.file_path.name}'"
        )
        return df

    def fetch_batch(self, start_idx: int = 0, batch_size: int = 100) -> pd.DataFrame:
        """
        Fetch a slice/batch of records to simulate streaming or incremental ingestion.
        
        Args:
            start_idx: Zero-based row index to begin reading.
            batch_size: Number of rows to retrieve.
            
        Returns:
            pd.DataFrame: Batch slice of raw records.
        """
        self.validate_source()
        df = pd.read_csv(
            self.file_path,
            skiprows=range(1, start_idx + 1) if start_idx > 0 else None,
            nrows=batch_size,
            encoding=self.encoding
        )
        return df
