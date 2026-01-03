"""
Tests for health endpoint.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test health check returns ok status."""
    async with async_client as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
