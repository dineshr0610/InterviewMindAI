"""
Core module — configuration, database, middleware, exceptions, logging, dependencies, and timing.
"""

from app.core.config import settings
from app.core.database import Base, engine, async_session_factory, get_db, init_db, close_db
from app.core.exceptions import (
    InterviewNotFoundException,
    InterviewAlreadyEndedException,
    InvalidAnswerException,
    AIProviderException,
    InterviewNotActiveException,
    DatabaseException,
)
from app.core.logging import setup_logging, get_logger
from app.core.middleware import setup_middleware
from app.core.dependencies import get_db_session
from app.core.timing import TimingContext, log_timing

__all__ = [
    "settings",
    "Base",
    "engine",
    "async_session_factory",
    "get_db",
    "init_db",
    "close_db",
    "InterviewNotFoundException",
    "InterviewAlreadyEndedException",
    "InvalidAnswerException",
    "AIProviderException",
    "InterviewNotActiveException",
    "DatabaseException",
    "setup_logging",
    "get_logger",
    "setup_middleware",
    "get_db_session",
    "TimingContext",
    "log_timing",
]
