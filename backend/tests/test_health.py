"""
Basic health check tests for the backend.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def client() -> AsyncClient:
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Test that the health endpoint returns a 200 status."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "checks" in data


@pytest.mark.asyncio
async def test_health_database_check(client: AsyncClient) -> None:
    """Test that health response includes database check."""
    response = await client.get("/api/health")
    data = response.json()
    assert "database" in data["checks"]
