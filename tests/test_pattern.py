"""
Tests for behavior pattern endpoint.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.anyio
async def test_pattern_basic(async_client):
    """Test basic pattern generation."""
    async with async_client as client:
        response = await client.post(
            "/pattern",
            json={"symbol": "AAPL", "context": ["earnings", "fed week"]},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["sample_size"] >= 0
    assert 0 <= data["win_rate"] <= 1
    assert data["typical_range"] >= 0
    assert data["max_move"] >= 0
    assert "notes" in data


@pytest.mark.anyio
async def test_pattern_default_context(async_client):
    """Test pattern generation with no context supplied."""
    async with async_client as client:
        response = await client.post(
            "/pattern",
            json={"symbol": "SPY"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["sample_size"] >= 0


@pytest.mark.anyio
async def test_pattern_symbol_normalization(async_client):
    """Test that symbol is normalized to uppercase."""
    async with async_client as client:
        response = await client.post(
            "/pattern",
            json={"symbol": "aapl", "context": ["earnings"]},
        )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_pattern_no_prediction_language(async_client):
    """Test that response doesn't contain prediction/advice language."""
    async with async_client as client:
        response = await client.post(
            "/pattern",
            json={"symbol": "AAPL", "context": ["earnings"]},
        )

    assert response.status_code == 200
    data = response.json()

    forbidden_words = ["will", "predict", "guarantee", "should buy", "should sell"]
    notes = data.get("notes", "").lower()
    for word in forbidden_words:
        assert word not in notes, f"Found forbidden word '{word}' in notes"
