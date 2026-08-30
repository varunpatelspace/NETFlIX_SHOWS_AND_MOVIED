"""
Unit Tests for Data Source Layer (pipeline/data_sources/).
"""

import os
import tempfile
import pytest
import pandas as pd

from pipeline.data_sources.base_source import BaseDataSource
from pipeline.data_sources.csv_source import CSVDataSource
from pipeline.data_sources.api_source import APIDataSource
from pipeline.data_sources.factory import get_data_source


def test_csv_data_source_with_existing_dataset():
    """Test CSVDataSource against the project's baseline Netflix dataset."""
    source = CSVDataSource(file_path="data/netflix_titles.csv")
    
    # 1. Validation
    assert source.validate_source() is True
    assert source.status == "validated"

    # 2. Raw Data Fetch
    df = source.fetch_raw_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5837
    assert "show_id" in df.columns
    assert "title" in df.columns
    assert "type" in df.columns

    # 3. Operational Metadata
    meta = source.get_metadata()
    assert meta["source_type"] == "csv"
    assert meta["status"] == "fetched"
    assert meta["record_count"] == 5837
    assert meta["last_fetched_at"] is not None
    assert len(meta["columns"]) == 12


def test_csv_data_source_batching():
    """Test simulated batch extraction for incremental streaming simulations."""
    source = CSVDataSource(file_path="data/netflix_titles.csv")
    batch = source.fetch_batch(start_idx=0, batch_size=25)
    assert len(batch) == 25
    assert "show_id" in batch.columns

    # Next batch
    batch2 = source.fetch_batch(start_idx=25, batch_size=25)
    assert len(batch2) == 25
    assert batch.iloc[0]["show_id"] != batch2.iloc[0]["show_id"]


def test_csv_data_source_missing_file():
    """Test that non-existent CSV file raises FileNotFoundError."""
    source = CSVDataSource(file_path="data/non_existent_file_12345.csv")
    with pytest.raises(FileNotFoundError):
        source.validate_source()


def test_csv_data_source_empty_file():
    """Test that an empty CSV file raises ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        source = CSVDataSource(file_path=tmp_path)
        with pytest.raises(ValueError, match="empty"):
            source.validate_source()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_api_data_source_with_mock_payload():
    """Test APIDataSource using mock payload."""
    mock_records = [
        {"show_id": "api_1", "title": "API Movie 1", "type": "Movie", "release_year": 2023},
        {"show_id": "api_2", "title": "API Series 1", "type": "TV Show", "release_year": 2024}
    ]
    api_source = APIDataSource(
        endpoint_url="https://api.example.com/netflix",
        mock_data=mock_records
    )

    assert api_source.validate_source() is True
    df = api_source.fetch_raw_data()
    assert len(df) == 2
    assert list(df["show_id"]) == ["api_1", "api_2"]
    
    meta = api_source.get_metadata()
    assert meta["source_type"] == "api"
    assert meta["record_count"] == 2


def test_data_source_factory():
    """Test factory instantiation of data sources based on configuration."""
    csv_src = get_data_source(source_type="csv", source_path="data/netflix_titles.csv")
    assert isinstance(csv_src, CSVDataSource)

    api_src = get_data_source(source_type="api")
    assert isinstance(api_src, APIDataSource)

    with pytest.raises(ValueError, match="Unsupported DATA_SOURCE_TYPE"):
        get_data_source(source_type="invalid_unknown_source")
