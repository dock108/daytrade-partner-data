"""
Tests for ticker endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_get_ticker_snapshot(async_client):
    """Test getting a ticker snapshot."""
    async with async_client as client:
        response = await client.get("/ticker/AAPL/snapshot")

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["company_name"] == "Apple Inc."
    assert data["sector"] == "Technology"
    assert "volatility" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_get_ticker_snapshot_not_found(async_client):
    """Test 404 for unknown ticker."""
    async with async_client as client:
        response = await client.get("/ticker/UNKNOWN/snapshot")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_ticker_history(async_client):
    """Test getting ticker price history."""
    async with async_client as client:
        response = await client.get("/ticker/NVDA/history?range=1M")

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "NVDA"
    assert "points" in data
    assert len(data["points"]) > 0
    assert "current_price" in data
    assert "change" in data
    assert "change_percent" in data


@pytest.mark.asyncio
async def test_get_ticker_history_different_ranges(async_client):
    """Test history with different time ranges."""
    async with async_client as client:
        for range_val in ["1D", "1M", "6M", "1Y"]:
            response = await client.get(f"/ticker/SPY/history?range={range_val}")
            assert response.status_code == 200

