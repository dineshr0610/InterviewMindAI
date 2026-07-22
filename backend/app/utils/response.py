"""
Utility functions for standardizing API responses.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import status
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """
    Create a standardized success response.

    Args:
        data: The response payload (optional).
        message: A success message.
        status_code: HTTP status code.

    Returns:
        A JSON response with standardized success format.
    """
    body: Dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        body["data"] = data

    return JSONResponse(content=body, status_code=status_code)


def error_response(
    message: str = "An error occurred",
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[str] = None,
    errors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.

    Args:
        message: A description of the error.
        error_code: A semantic error code for the error type.
        details: Additional details about the error (optional).
        errors: A list of specific error details (optional).

    Returns:
        A dictionary with standardized error format.
    """
    body: Dict[str, Any] = {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
    if details:
        body["details"] = details
    if errors:
        body["errors"] = errors

    return body


def health_response(
    status_str: str = "healthy",
    version: str = "1.0.0",
    database: str = "connected",
    ai_provider: str = "ready",
) -> Dict[str, Any]:
    """
    Create a health check response.

    Args:
        status_str: Overall service status.
        version: Application version.
        database: Database connection status.
        ai_provider: AI provider status.

    Returns:
        A dictionary with health information.
    """
    return {
        "status": status_str,
        "version": version,
        "checks": {
            "database": database,
            "ai_provider": ai_provider,
        },
    }
