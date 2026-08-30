"""
Automated unit tests for Dashboard Components, API Client, and Query Construction.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

from dashboard.components.api_client import ApiClient
from dashboard.components.charts import (
    plot_donut_chart,
    plot_horizontal_bar,
    plot_vertical_bar,
    plot_line_chart,
    plot_comparative_bars,
    plot_world_map
)


# -----------------------------------------------------------------------------
# 1. ApiClient Tests
# -----------------------------------------------------------------------------
def test_api_client_initialization():
    client = ApiClient(base_url="http://custom-host:9000", timeout=5)
    assert client.base_url == "http://custom-host:9000"
    assert client.timeout == 5


def test_api_client_connection_error():
    # Attempting to connect to an unreachable port should return a clean error dict, not raise
    client = ApiClient(base_url="http://127.0.0.1:59999", timeout=1)
    res = client.get_health()
    assert res["success"] is False
    assert "Cannot connect to API server" in res["error"]
    assert res["status_code"] == 0


def test_api_client_query_param_construction():
    client = ApiClient(base_url="http://127.0.0.1:8000")
    with patch.object(client.session, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total_titles": 100}
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        filters = {
            "content_type": "Movie",
            "release_year_min": 2018,
            "country": "India"
        }
        res = client.get_overview(filters=filters)

        assert res["success"] is True
        assert res["data"]["total_titles"] == 100
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8000/api/v1/analytics/overview",
            params=filters,
            timeout=15
        )


def test_api_client_refresh_pipeline_post():
    client = ApiClient(base_url="http://127.0.0.1:8000")
    with patch.object(client.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"final_status": "SUCCESS"}
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        res = client.refresh_pipeline(mode="upsert")
        assert res["success"] is True
        assert res["data"]["final_status"] == "SUCCESS"
        mock_post.assert_called_once_with(
            "http://127.0.0.1:8000/api/v1/pipeline/refresh",
            json={"mode": "upsert"},
            timeout=120
        )


# -----------------------------------------------------------------------------
# 2. Chart Generation Tests
# -----------------------------------------------------------------------------
def test_plotly_chart_constructors():
    # Donut
    fig1 = plot_donut_chart(["Movie", "TV Show"], [4000, 1800])
    assert fig1 is not None
    assert len(fig1.data) == 1

    # Horizontal Bar
    fig2 = plot_horizontal_bar(["Genre A", "Genre B"], [50, 30], title="Test Genres")
    assert fig2 is not None

    # Vertical Bar
    fig3 = plot_vertical_bar(["Jan", "Feb"], [10, 20], title="Test Months")
    assert fig3 is not None

    # Line Chart
    fig4 = plot_line_chart([2018, 2019, 2020], [100, 150, 200], title="Test Growth")
    assert fig4 is not None

    # Comparative Bar
    fig5 = plot_comparative_bars([2019, 2020], [80, 100], [20, 50], title="Test Comp")
    assert fig5 is not None

    # World Map
    fig6 = plot_world_map(["United States", "India"], [2400, 750], title="Test Map")
    assert fig6 is not None
