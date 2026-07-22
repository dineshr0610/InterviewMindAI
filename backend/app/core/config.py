"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from __future__ import annotations

from typing import ClassVar, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All values have defaults for local development.
    """

    # Application
    APP_NAME: str = "InterviewMind AI Backend"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI Mock Interview Platform Backend"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Connection URLs
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interviewmind"
    DIRECT_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interviewmind"
    DATABASE_ECHO: bool = False

    # Supabase Credentials
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""

    # AI Integration (Gemini / LangGraph)
    GEMINI_API_KEY: str = ""

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Interview Defaults & Adaptive Difficulty Thresholds
    DEFAULT_MAX_QUESTIONS: int = 5
    DEFAULT_DIFFICULTY: str = "Easy"
    SCORE_UPGRADE_THRESHOLD: int = 8
    SCORE_DOWNGRADE_THRESHOLD: int = 4

    model_config: ClassVar[dict] = {
        "env_file": [".env", "backend/.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
