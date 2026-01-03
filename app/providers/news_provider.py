"""
Canonical news data provider — single source of truth for market news.

All news data in the application MUST come through this provider.
Currently a placeholder — will integrate with news APIs when available.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.logging import get_logger
from app.providers.cache import cache

logger = get_logger(__name__)

SOURCE = "mock"  # Will change when real news API is integrated


@dataclass
class NewsItem:
    """A single news article."""

    title: str
    summary: str
    source: str
    published_at: datetime
    url: str | None = None
    sentiment: str | None = None  # "positive", "negative", "neutral"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "publishedAt": self.published_at.isoformat(),
            "url": self.url,
            "sentiment": self.sentiment,
        }


@dataclass
class NewsData:
    """
    Canonical news data structure.

    All endpoints receiving news data get this exact shape.
    """

    ticker: str | None  # None for general market news
    items: list[NewsItem]
    timestamp: datetime
    source: str = SOURCE

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "items": [item.to_dict() for item in self.items],
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


class NewsProvider:
    """
    Canonical provider for news data.

    Currently returns mock data. Will integrate with:
    - Yahoo Finance news
    - Alpha Vantage news
    - NewsAPI
    - Or other news providers

    Usage:
        provider = NewsProvider()
        news = await provider.get_news("AAPL")
    """

    # Mock news templates
    _MOCK_HEADLINES = [
        ("Company reports quarterly earnings", "neutral"),
        ("Analysts maintain outlook on stock", "neutral"),
        ("Sector sees mixed trading activity", "neutral"),
        ("Market volatility continues amid economic data", "neutral"),
        ("Investors watch Fed policy developments", "neutral"),
    ]

    async def get_news(
        self,
        symbol: str | None = None,
        limit: int = 5,
        use_cache: bool = True,
    ) -> NewsData:
        """
        Get news for a symbol or general market news.

        Args:
            symbol: Ticker symbol (optional, None for market news)
            limit: Maximum number of articles
            use_cache: Whether to use cached data (default True)

        Returns:
            NewsData with news items
        """
        symbol = symbol.upper() if symbol else None

        # Check cache first
        if use_cache:
            cached = cache.get_news(symbol)
            if cached:
                logger.debug(f"Cache hit for news:{symbol or 'market'}")
                return cached

        # Generate mock news (placeholder)
        data = self._get_mock_news(symbol, limit)

        # Cache the result
        cache.set_news(data, symbol)
        logger.info(f"Fetched news for {symbol or 'market'}: {len(data.items)} items")

        return data

    def _get_mock_news(self, symbol: str | None, limit: int) -> NewsData:
        """Generate mock news data."""
        import random

        items: list[NewsItem] = []
        now = datetime.now(UTC)

        for i in range(min(limit, len(self._MOCK_HEADLINES))):
            headline, sentiment = self._MOCK_HEADLINES[i]

            # Customize headline for symbol
            if symbol:
                headline = headline.replace("Company", symbol).replace("stock", f"{symbol} stock")

            items.append(
                NewsItem(
                    title=headline,
                    summary="Market analysis and commentary on recent developments. "
                    "Investors continue to monitor key indicators.",
                    source=random.choice(["Reuters", "Bloomberg", "MarketWatch", "CNBC"]),
                    published_at=now - timedelta(hours=random.randint(1, 48)),
                    url=None,
                    sentiment=sentiment,
                )
            )

        return NewsData(
            ticker=symbol,
            items=items,
            timestamp=now,
        )

