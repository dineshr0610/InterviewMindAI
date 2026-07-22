"""
InterviewMind AI Backend — FastAPI Application Entry Point.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
workspace_dir = backend_dir.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import health_router, interview_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import BaseInterviewException
from app.core.logging import get_logger, setup_logging
from app.core.middleware import setup_middleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.

    On startup:
        - Sets up logging
        - Initializes database engine & tables
    On shutdown:
        - Disposes database connection pool
    """
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.warning("Database initialization skipped: %s", exc)
        logger.info("Will connect on first database access.")

    yield

    logger.info("Shutting down %s...", settings.APP_NAME)
    await close_db()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Application factory function.
    Creates and configures FastAPI application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure middleware
    setup_middleware(app)

    # Register routers
    app.include_router(health_router)
    app.include_router(interview_router)

    # Register global exception handlers
    _register_exception_handlers(app)

    logger.info("Application created successfully.")
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers for application.
    Ensures all errors return consistent, structured JSON responses.
    """

    @app.exception_handler(BaseInterviewException)
    async def base_interview_exception_handler(
        request: Request, exc: BaseInterviewException
    ) -> JSONResponse:
        logger.warning("Domain exception [%s]: %s", exc.error_code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "error_code": exc.error_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "")
            errors.append({"field": field, "message": msg})

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "errors": errors,
                "error_code": "VALIDATION_ERROR",
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error_code": "HTTP_ERROR",
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled internal exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected internal error occurred.",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )

    logger.info("Global exception handlers registered successfully.")


# Create default application instance
app = create_app()
