"""
Reusable API Client for communicating with the FastAPI Backend.
"""

import os
import requests
from typing import Dict, Any, Optional, List
from config.settings import API_BASE_URL


class ApiClient:
    """
    HTTP client for the Netflix Live Content Analytics API.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 15):
        self.base_url = (base_url or os.getenv("API_BASE_URL", API_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper for GET requests with clean error catching."""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return {"success": True, "data": resp.json(), "status_code": resp.status_code}
        except requests.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to API server at {self.base_url}. Please ensure FastAPI is running.",
                "status_code": 0
            }
        except requests.Timeout:
            return {
                "success": False,
                "error": "API request timed out. The server took too long to respond.",
                "status_code": 408
            }
        except requests.HTTPError as e:
            detail = resp.json().get("detail", str(e)) if resp.text else str(e)
            return {
                "success": False,
                "error": detail,
                "status_code": resp.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": 500
            }

    def _post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, timeout: int = 60) -> Dict[str, Any]:
        """Helper for POST requests."""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.post(url, json=json_data or {}, timeout=timeout)
            resp.raise_for_status()
            return {"success": True, "data": resp.json(), "status_code": resp.status_code}
        except requests.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to API server at {self.base_url}.",
                "status_code": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }

    # -------------------------------------------------------------------------
    # API Methods
    # -------------------------------------------------------------------------

    def get_health(self) -> Dict[str, Any]:
        """Fetch system health status."""
        return self._get("/health")

    def get_dashboard_summary(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch master dashboard consolidated summary."""
        return self._get("/api/v1/dashboard/summary", params=filters)

    def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch catalog overview metrics."""
        return self._get("/api/v1/analytics/overview", params=filters)

    def get_content_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch content format & genre distribution."""
        return self._get("/api/v1/analytics/content", params=filters)

    def get_temporal_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch temporal trends and seasonality."""
        return self._get("/api/v1/analytics/temporal", params=filters)

    def get_geographic_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch territory production and co-productions."""
        return self._get("/api/v1/analytics/geographic", params=filters)

    def get_rating_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch maturity certifications and audience tiers."""
        return self._get("/api/v1/analytics/ratings", params=filters)

    def get_duration_analysis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch movie runtime & TV show season stats."""
        return self._get("/api/v1/analytics/duration", params=filters)

    def get_insights(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch rule-based business insights."""
        return self._get("/api/v1/analytics/insights", params=filters)

    def get_content(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch paginated content titles."""
        params = dict(filters or {})
        params["limit"] = limit
        params["offset"] = offset
        if search:
            params["search"] = search
        return self._get("/api/v1/content", params=params)

    def get_content_detail(self, show_id: str) -> Dict[str, Any]:
        """Fetch details for a single show_id."""
        return self._get(f"/api/v1/content/{show_id}")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Fetch current pipeline state and config."""
        return self._get("/api/v1/pipeline/status")

    def refresh_pipeline(self, mode: str = "insert_new_only") -> Dict[str, Any]:
        """Trigger on-demand ETL ingestion."""
        return self._post("/api/v1/pipeline/refresh", json_data={"mode": mode}, timeout=120)

    def get_pipeline_history(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch paginated pipeline execution audit history."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status and status != "All":
            params["status"] = status
        return self._get("/api/v1/pipeline/history", params=params)

    def get_pipeline_history_detail(self, run_id: str) -> Dict[str, Any]:
        """Fetch full details for a specific pipeline execution."""
        return self._get(f"/api/v1/pipeline/history/{run_id}")

    def get_automation_status(self) -> Dict[str, Any]:
        """Fetch scheduler state, next execution time, and background run status."""
        return self._get("/api/v1/automation/status")
