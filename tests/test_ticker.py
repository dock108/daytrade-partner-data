"""
Tests for market/ticker endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


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
    assert "company_name" in data
    assert "sector" in data
    assert "volatility" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_get_ticker_snapshot_not_found(async_client):
    """
    Test unknown ticker handling.

    In mock mode, providers return synthetic data for any symbol.
    In live mode (USE_MOCK_DATA=false), this would return 404.
    """
    async with async_client as client:
        response = await client.get("/ticker/XYZNOTREAL123/snapshot")

    # Mock mode returns 200 with generated data; live mode returns 404
    # Since tests run with USE_MOCK_DATA=true, expect 200
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "XYZNOTREAL123"


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


@pytest.mark.asyncio
async def test_ticker_snapshot_has_price_fields(async_client):
    """Test that snapshot includes price-related fields."""
    async with async_client as client:
        response = await client.get("/ticker/AAPL/snapshot")

    assert response.status_code == 200
    data = response.json()
    # These fields may be null but should exist
    assert "current_price" in data
    assert "change_percent" in data
    assert "week_52_high" in data
    assert "week_52_low" in data


@pytest.mark.asyncio
async def test_history_points_have_required_fields(async_client):
    """Test that history points have date, close, high, low."""
    async with async_client as client:
        response = await client.get("/ticker/QQQ/history?range=1M")

    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) > 0

    point = data["points"][0]
    assert "date" in point
    assert "close" in point
    assert "high" in point
    assert "low" in point
