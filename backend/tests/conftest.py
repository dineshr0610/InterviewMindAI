"""
Pytest configuration and shared fixtures for backend testing.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_gemini_llm(monkeypatch):
    """Globally mock Gemini LLM calls during tests to prevent quota usage."""
    class MockResponse:
        def __init__(self, content):
            self.content = content
    
    def mock_invoke(*args, **kwargs):
        return MockResponse('{"summary": "Mock summary", "core_requirements": [{"requirement": "Mock Req", "status": "missing_evidence", "confidence": 0.0}]}')
        
    try:
        from ai_engine.models.llm import PoolableLLM
        monkeypatch.setattr(PoolableLLM, "invoke", mock_invoke)
    except ImportError:
        pass


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client for API testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
