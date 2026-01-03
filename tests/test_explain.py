"""
Tests for /explain endpoint.
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
async def test_explain_with_symbol(async_client):
    """Test explanation with a symbol provided."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={
                "question": "What's happening with AAPL?",
                "symbol": "AAPL",
                "timeframeDays": 30,
                "simpleMode": False,
            },
        )

    assert response.status_code == 200
    data = response.json()

    # All 5 fields should be populated
    assert data["question"] == "What's happening with AAPL?"
    assert data["symbol"] == "AAPL"
    assert "whatsHappeningNow" in data and len(data["whatsHappeningNow"]) > 0
    assert "keyDrivers" in data and len(data["keyDrivers"]) > 0
    assert "riskVsOpportunity" in data and len(data["riskVsOpportunity"]) > 0
    assert "historicalBehavior" in data and len(data["historicalBehavior"]) > 0
    assert "simpleRecap" in data and len(data["simpleRecap"]) > 0
    assert "generatedAt" in data


@pytest.mark.asyncio
async def test_explain_without_symbol(async_client):
    """Test explanation without a symbol (generic market question)."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={"question": "How do interest rates affect stocks?"},
        )

    assert response.status_code == 200
    data = response.json()

    # All 5 fields should be populated even without symbol
    assert data["symbol"] is None
    assert "whatsHappeningNow" in data and len(data["whatsHappeningNow"]) > 0
    assert "keyDrivers" in data and len(data["keyDrivers"]) > 0
    assert "riskVsOpportunity" in data and len(data["riskVsOpportunity"]) > 0
    assert "historicalBehavior" in data and len(data["historicalBehavior"]) > 0
    assert "simpleRecap" in data and len(data["simpleRecap"]) > 0


@pytest.mark.asyncio
async def test_explain_simple_mode(async_client):
    """Test explanation with simple mode enabled."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={
                "question": "What is happening with SPY?",
                "symbol": "SPY",
                "simpleMode": True,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "simpleRecap" in data


@pytest.mark.asyncio
async def test_explain_no_recommendation_language(async_client):
    """Test that response doesn't contain buy/sell recommendations."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={
                "question": "Should I buy NVDA?",
                "symbol": "NVDA",
            },
        )

    assert response.status_code == 200
    data = response.json()

    # Combine all text fields
    all_text = " ".join(
        [
            data.get("whatsHappeningNow", ""),
            data.get("riskVsOpportunity", ""),
            data.get("historicalBehavior", ""),
            data.get("simpleRecap", ""),
        ]
    ).lower()

    # Check for forbidden recommendation language
    forbidden_phrases = ["you should buy", "you should sell", "i recommend", "buy now", "sell now"]
    for phrase in forbidden_phrases:
        assert phrase not in all_text, f"Found forbidden phrase '{phrase}' in response"


@pytest.mark.asyncio
async def test_explain_empty_question_fails(async_client):
    """Test that empty question is rejected."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={"question": ""},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_explain_question_too_long_fails(async_client):
    """Test that overly long question is rejected."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={"question": "x" * 501},  # Over 500 char limit
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_explain_invalid_timeframe_fails(async_client):
    """Test that invalid timeframe is rejected."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={
                "question": "What about AAPL?",
                "symbol": "AAPL",
                "timeframeDays": 5,  # Below minimum of 10
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_explain_fallback_prevents_500(async_client):
    """Test that fallback logic prevents 500 errors for unknown symbols."""
    async with async_client as client:
        response = await client.post(
            "/explain",
            json={
                "question": "What's happening with this random ticker?",
                "symbol": "XYZNOTREAL123",
            },
        )

    # Should not return 500 - fallback should handle gracefully
    assert response.status_code == 200
    data = response.json()
    # Generic response should still have all fields
    assert "whatsHappeningNow" in data
    assert "keyDrivers" in data
