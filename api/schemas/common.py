"""
Common schemas for Netflix Live Content Analytics API.
"""

from pydantic import BaseModel
from typing import Optional, Any


class ErrorResponse(BaseModel):
    """Structured error response format."""
    detail: str
    error_code: str


class SuccessResponse(BaseModel):
    """Standard success confirmation."""
    message: str
    status: str = "success"
