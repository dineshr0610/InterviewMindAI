"""
API Routes package — registers all route handlers.
"""

from app.api.routes.health import router as health_router
from app.api.routes.interview import router as interview_router

__all__ = ["health_router", "interview_router"]
