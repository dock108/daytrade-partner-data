"""
Tests for outlook endpoint.
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
async def test_outlook_basic(async_client):
    """Test basic outlook generation."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "AAPL", "timeframeDays": 30},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["timeframe_days"] == 30
    assert data["sentiment_summary"] in ["positive", "mixed", "cautious"]
    assert "key_drivers" in data
    assert len(data["key_drivers"]) > 0
    assert "volatility_band" in data
    assert "historical_hit_rate" in data
    assert 0 <= data["historical_hit_rate"] <= 1


@pytest.mark.asyncio
async def test_outlook_default_timeframe(async_client):
    """Test outlook with default timeframe (30 days)."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "SPY"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["timeframe_days"] == 30


@pytest.mark.asyncio
async def test_outlook_custom_timeframe(async_client):
    """Test outlook with custom timeframe."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "QQQ", "timeframeDays": 90},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["timeframe_days"] == 90


@pytest.mark.asyncio
async def test_outlook_validation_timeframe_too_low(async_client):
    """Test validation: timeframe < 10 should fail."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "AAPL", "timeframeDays": 5},
        )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_outlook_validation_timeframe_too_high(async_client):
    """Test validation: timeframe > 365 should fail."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "AAPL", "timeframeDays": 500},
        )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_outlook_unknown_symbol_in_mock_mode(async_client):
    """Test that unknown symbols still work in mock mode (with generated data)."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "XYZNOTREAL123", "timeframeDays": 30},
        )

    # In mock mode, unknown symbols get generated data
    # In live mode, this would return 404
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "XYZNOTREAL123"
    assert "historical_hit_rate" in data


@pytest.mark.asyncio
async def test_outlook_symbol_normalization(async_client):
    """Test that symbol is normalized to uppercase."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "aapl", "timeframeDays": 30},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_outlook_no_prediction_language(async_client):
    """Test that response doesn't contain prediction/advice language."""
    async with async_client as client:
        response = await client.post(
            "/outlook",
            json={"symbol": "AAPL", "timeframeDays": 30},
        )

    assert response.status_code == 200
    data = response.json()

    # Combine all text fields to check for forbidden language
    all_text = " ".join(
        [
            data.get("personal_context") or "",
            data.get("volatility_warning") or "",
            data.get("timeframe_note") or "",
            *data.get("key_drivers", []),
        ]
    ).lower()

    # No prediction/advice language
    forbidden_words = ["will", "predict", "guarantee", "should buy", "should sell", "recommend"]
    for word in forbidden_words:
        assert word not in all_text, f"Found forbidden word '{word}' in response"


@pytest.mark.asyncio
async def test_outlook_composer_with_metadata(async_client):
    """Test composed outlook endpoint returns metadata."""
    async with async_client as client:
        response = await client.get("/outlook/AAPL")

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert "big_picture" in data
    assert "what_could_move_it" in data
    assert "expected_swings" in data
    assert "historical_behavior" in data
    assert "recent_articles" in data
    assert "timestamps" in data
    assert "data_sources" in data

    timestamps = data["timestamps"]
    sources = data["data_sources"]
    for key in ["snapshot", "history", "catalysts", "news", "patterns", "generated_at"]:
        assert key in timestamps
    for key in ["snapshot", "history", "catalysts", "news", "patterns"]:
        assert key in sources
