"""
Canonical price data provider — single source of truth for current prices.

All price data in the application MUST come through this provider.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import yfinance as yf

from app.core.config import settings
from app.core.errors import ExternalServiceError, TickerNotFoundError
from app.core.logging import get_logger
from app.providers.cache import cache

logger = get_logger(__name__)

# Source identifier for all data from this provider
SOURCE = "yfinance"


@dataclass
class PriceData:
    """
    Canonical price data structure.

    All endpoints receiving price data get this exact shape.
    """

    ticker: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    day_high: float
    day_low: float
    week_52_high: float
    week_52_low: float
    volume: int
    market_cap: int | None
    timestamp: datetime
    source: str = SOURCE

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "currentPrice": self.current_price,
            "previousClose": self.previous_close,
            "change": self.change,
            "changePercent": self.change_percent,
            "dayHigh": self.day_high,
            "dayLow": self.day_low,
            "week52High": self.week_52_high,
            "week52Low": self.week_52_low,
            "volume": self.volume,
            "marketCap": self.market_cap,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


class PriceProvider:
    """
    Canonical provider for current price data.

    Usage:
        provider = PriceProvider()
        price = await provider.get_price("AAPL")
    """

    # Mock data for testing
    _MOCK_PRICES: dict[str, dict] = {
        "AAPL": {"price": 185.0, "prev": 183.5, "high": 186.2, "low": 184.1, "w52h": 231.25, "w52l": 138.75},
        "NVDA": {"price": 485.0, "prev": 478.0, "high": 490.5, "low": 476.3, "w52h": 520.0, "w52l": 220.0},
        "SPY": {"price": 475.0, "prev": 473.2, "high": 476.8, "low": 472.5, "w52h": 495.0, "w52l": 410.0},
        "QQQ": {"price": 405.0, "prev": 402.5, "high": 407.3, "low": 401.2, "w52h": 430.0, "w52l": 340.0},
        "TSLA": {"price": 245.0, "prev": 248.0, "high": 252.0, "low": 243.5, "w52h": 290.0, "w52l": 150.0},
    }

    async def get_price(self, symbol: str, use_cache: bool = True) -> PriceData:
        """
        Get current price data for a symbol.

        Args:
            symbol: Ticker symbol (e.g., AAPL)
            use_cache: Whether to use cached data (default True)

        Returns:
            PriceData with current market data

        Raises:
            TickerNotFoundError: Symbol not found
            ExternalServiceError: Provider unavailable
        """
        symbol = symbol.upper()

        # Check cache first
        if use_cache:
            cached = cache.get_price(symbol)
            if cached:
                logger.debug(f"Cache hit for price:{symbol}")
                return cached

        # Fetch from source
        if settings.USE_MOCK_DATA:
            data = self._get_mock_price(symbol)
        else:
            data = self._get_yfinance_price(symbol)

        # Cache the result
        cache.set_price(symbol, data)
        logger.info(f"Fetched price for {symbol}: ${data.current_price}")

        return data

    def _get_yfinance_price(self, symbol: str) -> PriceData:
        """Fetch price from yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info.get("regularMarketPrice") is None:
                raise TickerNotFoundError(symbol)

            current_price = info.get("regularMarketPrice") or info.get("previousClose", 0)
            previous_close = info.get("previousClose", current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0

            return PriceData(
                ticker=symbol,
                current_price=round(current_price, 2),
                previous_close=round(previous_close, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                day_high=round(info.get("dayHigh", current_price), 2),
                day_low=round(info.get("dayLow", current_price), 2),
                week_52_high=round(info.get("fiftyTwoWeekHigh", current_price), 2),
                week_52_low=round(info.get("fiftyTwoWeekLow", current_price), 2),
                volume=info.get("volume", 0) or 0,
                market_cap=info.get("marketCap"),
                timestamp=datetime.now(UTC),
            )

        except TickerNotFoundError:
            raise
        except Exception as e:
            logger.error(f"yfinance price error for {symbol}: {e}")
            raise ExternalServiceError("yfinance", "Failed to fetch price data")

    def _get_mock_price(self, symbol: str) -> PriceData:
        """Generate mock price data."""
        import random

        mock = self._MOCK_PRICES.get(symbol)
        if not mock:
            # Generate random mock for unknown symbols
            base = random.uniform(50, 500)
            mock = {
                "price": base,
                "prev": base * 0.99,
                "high": base * 1.02,
                "low": base * 0.98,
                "w52h": base * 1.25,
                "w52l": base * 0.75,
            }

        price = mock["price"] * random.uniform(0.99, 1.01)
        prev = mock["prev"]
        change = price - prev

        return PriceData(
            ticker=symbol,
            current_price=round(price, 2),
            previous_close=round(prev, 2),
            change=round(change, 2),
            change_percent=round((change / prev) * 100, 2),
            day_high=round(mock["high"], 2),
            day_low=round(mock["low"], 2),
            week_52_high=round(mock["w52h"], 2),
            week_52_low=round(mock["w52l"], 2),
            volume=random.randint(1_000_000, 50_000_000),
            market_cap=random.randint(100_000_000_000, 3_000_000_000_000),
            timestamp=datetime.now(UTC),
        )

