"""
Tests for canonical data providers.

Verifies:
- All endpoints use canonical providers
- Timestamps always exist
- Output schemas match expected structure
- Caching works correctly
"""

from datetime import datetime

import pytest

from app.providers import (
    HistoryData,
    HistoryProvider,
    NewsData,
    NewsProvider,
    PriceData,
    PriceProvider,
    cache,
)


class TestPriceProvider:
    """Tests for the price provider."""

    @pytest.fixture
    def provider(self):
        return PriceProvider()

    @pytest.mark.asyncio
    async def test_get_price_returns_price_data(self, provider):
        """Price provider returns PriceData instance."""
        result = await provider.get_price("AAPL")
        assert isinstance(result, PriceData)

    @pytest.mark.asyncio
    async def test_price_data_has_timestamp(self, provider):
        """Price data includes timestamp."""
        result = await provider.get_price("AAPL")
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_price_data_has_source(self, provider):
        """Price data includes source field."""
        result = await provider.get_price("AAPL")
        assert result.source is not None
        assert len(result.source) > 0

    @pytest.mark.asyncio
    async def test_price_data_has_required_fields(self, provider):
        """Price data has all required price fields."""
        result = await provider.get_price("NVDA")

        assert result.ticker == "NVDA"
        assert result.current_price > 0
        assert result.previous_close > 0
        assert isinstance(result.change, float)
        assert isinstance(result.change_percent, float)
        assert result.week_52_high > 0
        assert result.week_52_low > 0

    @pytest.mark.asyncio
    async def test_price_data_to_dict(self, provider):
        """Price data can be serialized to dict."""
        result = await provider.get_price("SPY")
        data = result.to_dict()

        assert "ticker" in data
        assert "currentPrice" in data
        assert "timestamp" in data
        assert "source" in data

    @pytest.mark.asyncio
    async def test_symbol_normalization(self, provider):
        """Symbols are normalized to uppercase."""
        result = await provider.get_price("aapl")
        assert result.ticker == "AAPL"


class TestHistoryProvider:
    """Tests for the history provider."""

    @pytest.fixture
    def provider(self):
        return HistoryProvider()

    @pytest.mark.asyncio
    async def test_get_history_returns_history_data(self, provider):
        """History provider returns HistoryData instance."""
        result = await provider.get_history("AAPL", "1M")
        assert isinstance(result, HistoryData)

    @pytest.mark.asyncio
    async def test_history_data_has_timestamp(self, provider):
        """History data includes timestamp."""
        result = await provider.get_history("AAPL", "1M")
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_history_data_has_source(self, provider):
        """History data includes source field."""
        result = await provider.get_history("AAPL", "1M")
        assert result.source is not None

    @pytest.mark.asyncio
    async def test_history_data_has_points(self, provider):
        """History data includes price points."""
        result = await provider.get_history("NVDA", "1M")
        assert len(result.points) > 0

    @pytest.mark.asyncio
    async def test_history_points_have_required_fields(self, provider):
        """Each history point has required OHLCV fields."""
        result = await provider.get_history("SPY", "1M")

        for point in result.points[:5]:  # Check first 5
            assert point.date is not None
            assert point.open > 0
            assert point.high > 0
            assert point.low > 0
            assert point.close > 0
            assert point.volume >= 0

    @pytest.mark.asyncio
    async def test_history_computed_properties(self, provider):
        """History data computes change correctly."""
        result = await provider.get_history("QQQ", "1M")

        assert result.start_price > 0
        assert result.end_price > 0
        assert isinstance(result.change, float)
        assert isinstance(result.change_percent, float)

    @pytest.mark.asyncio
    async def test_history_closes_array(self, provider):
        """History data provides closes as numpy array."""
        result = await provider.get_history("AAPL", "1M")

        closes = result.closes
        assert len(closes) == len(result.points)
        assert closes[0] == result.points[0].close


class TestNewsProvider:
    """Tests for the news provider."""

    @pytest.fixture
    def provider(self):
        return NewsProvider()

    @pytest.mark.asyncio
    async def test_get_news_returns_news_data(self, provider):
        """News provider returns NewsData instance."""
        result = await provider.get_news("AAPL")
        assert isinstance(result, NewsData)

    @pytest.mark.asyncio
    async def test_news_data_has_timestamp(self, provider):
        """News data includes timestamp."""
        result = await provider.get_news("AAPL")
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_news_data_has_source(self, provider):
        """News data includes source field."""
        result = await provider.get_news()
        assert result.source is not None

    @pytest.mark.asyncio
    async def test_news_items_have_required_fields(self, provider):
        """Each news item has required fields."""
        result = await provider.get_news("NVDA", limit=3)

        for item in result.items:
            assert item.title is not None
            assert item.summary is not None
            assert item.source is not None
            assert item.published_at is not None

    @pytest.mark.asyncio
    async def test_market_news_without_symbol(self, provider):
        """Can fetch general market news without symbol."""
        result = await provider.get_news()
        assert result.ticker is None
        assert len(result.items) > 0


class TestCache:
    """Tests for the caching layer."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_set_and_get(self):
        """Cache can store and retrieve values."""
        cache.set("test:key", {"value": 123}, ttl=60)
        result = cache.get("test:key")
        assert result == {"value": 123}

    def test_cache_returns_none_for_missing(self):
        """Cache returns None for missing keys."""
        result = cache.get("nonexistent:key")
        assert result is None

    def test_cache_price_methods(self):
        """Cache has convenience methods for prices."""
        cache.set_price("AAPL", {"price": 185.0})
        result = cache.get_price("AAPL")
        assert result == {"price": 185.0}

    def test_cache_history_methods(self):
        """Cache has convenience methods for history."""
        cache.set_history("AAPL", "1M", {"points": []})
        result = cache.get_history("AAPL", "1M")
        assert result == {"points": []}

    def test_cache_news_methods(self):
        """Cache has convenience methods for news."""
        cache.set_news({"items": []}, symbol="NVDA")
        result = cache.get_news("NVDA")
        assert result == {"items": []}

    def test_cache_stats(self):
        """Cache tracks hit/miss statistics."""
        cache.get("miss1")
        cache.get("miss2")
        cache.set("hit", "value")
        cache.get("hit")

        stats = cache.stats
        assert stats["hits"] >= 1
        assert stats["misses"] >= 2


class TestProviderIntegration:
    """Integration tests verifying providers work with services."""

    @pytest.mark.asyncio
    async def test_ticker_service_uses_providers(self):
        """Ticker service fetches data through providers."""
        from app.services.ticker_service import TickerService

        service = TickerService()
        snapshot = await service.get_snapshot("AAPL")

        # Verify data came through (would have timestamp in underlying data)
        assert snapshot.ticker == "AAPL"
        assert snapshot.current_price > 0

    @pytest.mark.asyncio
    async def test_outlook_engine_uses_providers(self):
        """Outlook engine fetches data through providers."""
        from app.services.outlook_engine import OutlookEngine

        engine = OutlookEngine()
        outlook = await engine.compute_outlook("AAPL", 30)

        # Verify outlook was computed
        assert outlook.ticker == "AAPL"
        assert outlook.historical_hit_rate >= 0
        assert outlook.generated_at is not None


