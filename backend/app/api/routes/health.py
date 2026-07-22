"""
Health check endpoint.
Provides a simple health check for monitoring and load balancers.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.utils.response import health_response

logger = logging.getLogger("interviewmind.routes.health")
router = APIRouter(tags=["Health"])


@router.get(
    "/api/health",
    summary="Health Check",
    description="Check if the backend service and its dependencies are operational.",
)
async def health_check():
    """
    Health check endpoint.

    Returns the status of the application, database, and AI provider.
    This is useful for monitoring, load balancers, and Kubernetes probes.
    """
    logger.debug("Health check requested.")
    return health_response()
