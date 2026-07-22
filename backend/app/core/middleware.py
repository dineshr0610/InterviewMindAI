"""
FastAPI middleware for CORS, logging, request ID tracking, and error handling.
"""

from __future__ import annotations

import uuid
import time
import logging
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger("interviewmind.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all incoming requests and outgoing responses
    with execution time and request ID.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Add request ID to request state for use in routes
        request.state.request_id = request_id

        logger.info(
            "-> [%s] %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response: Response = await call_next(request)
            elapsed = time.time() - start_time

            logger.info(
                "<- [%s] %s %s | Status: %d | Time: %.3fs",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )

            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error(
                "[ERROR] [%s] %s %s | Error: %s | Time: %.3fs",
                request_id,
                request.method,
                request.url.path,
                str(exc),
                elapsed,
            )
            raise


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # CORS middleware (must be added last so it runs first on incoming requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:[0-9]+)?",
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    logger.info("Middleware configured successfully.")
