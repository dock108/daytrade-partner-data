"""
Canonical historical data provider — single source of truth for price history.

All historical price data in the application MUST come through this provider.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np
import yfinance as yf

from app.core.config import settings
from app.core.errors import ExternalServiceError, TickerNotFoundError
from app.core.logging import get_logger
from app.providers.cache import cache

logger = get_logger(__name__)

SOURCE = "yfinance"


@dataclass
class HistoryPoint:
    """A single price point in history."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class HistoryData:
    """
    Canonical historical data structure.

    All endpoints receiving history data get this exact shape.
    """

    ticker: str
    period: str
    interval: str
    points: list[HistoryPoint]
    timestamp: datetime
    source: str = SOURCE

    # Computed properties
    @property
    def start_price(self) -> float:
        return self.points[0].close if self.points else 0

    @property
    def end_price(self) -> float:
        return self.points[-1].close if self.points else 0

    @property
    def change(self) -> float:
        return round(self.end_price - self.start_price, 2)

    @property
    def change_percent(self) -> float:
        if self.start_price == 0:
            return 0
        return round((self.change / self.start_price) * 100, 2)

    @property
    def closes(self) -> np.ndarray:
        """Return close prices as numpy array for analysis."""
        return np.array([p.close for p in self.points])

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "period": self.period,
            "interval": self.interval,
            "points": [p.to_dict() for p in self.points],
            "startPrice": self.start_price,
            "endPrice": self.end_price,
            "change": self.change,
            "changePercent": self.change_percent,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


# Period to yfinance mapping
PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "1W": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "3Y": ("3y", "1d"),
    "5Y": ("5y", "1wk"),
}


class HistoryProvider:
    """
    Canonical provider for historical price data.

    Usage:
        provider = HistoryProvider()
        history = await provider.get_history("AAPL", "1M")
    """

    async def get_history(
        self,
        symbol: str,
        period: str = "1M",
        use_cache: bool = True,
    ) -> HistoryData:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Ticker symbol (e.g., AAPL)
            period: Time period (1D, 1W, 1M, 3M, 6M, 1Y, 3Y, 5Y)
            use_cache: Whether to use cached data (default True)

        Returns:
            HistoryData with price history

        Raises:
            TickerNotFoundError: Symbol not found
            ExternalServiceError: Provider unavailable
        """
        symbol = symbol.upper()
        period = period.upper()

        if period not in PERIOD_MAP:
            period = "1M"

        # Check cache first
        if use_cache:
            cached = cache.get_history(symbol, period)
            if cached:
                logger.debug(f"Cache hit for history:{symbol}:{period}")
                return cached

        # Fetch from source
        if settings.USE_MOCK_DATA:
            data = self._get_mock_history(symbol, period)
        else:
            data = self._get_yfinance_history(symbol, period)

        # Cache the result
        cache.set_history(symbol, period, data)
        logger.info(f"Fetched {period} history for {symbol}: {len(data.points)} points")

        return data

    def _get_yfinance_history(self, symbol: str, period: str) -> HistoryData:
        """Fetch history from yfinance."""
        try:
            yf_period, yf_interval = PERIOD_MAP.get(period, ("1mo", "1d"))

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=yf_period, interval=yf_interval)

            if hist.empty:
                raise TickerNotFoundError(symbol)

            points: list[HistoryPoint] = []
            for idx, row in hist.iterrows():
                # Convert index to UTC datetime
                if hasattr(idx, "tz_convert"):
                    dt = idx.tz_convert("UTC").to_pydatetime()
                elif hasattr(idx, "to_pydatetime"):
                    dt = idx.to_pydatetime()
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                else:
                    dt = datetime.fromisoformat(str(idx)).replace(tzinfo=UTC)

                points.append(
                    HistoryPoint(
                        date=dt,
                        open=round(float(row["Open"]), 2),
                        high=round(float(row["High"]), 2),
                        low=round(float(row["Low"]), 2),
                        close=round(float(row["Close"]), 2),
                        volume=int(row["Volume"]),
                    )
                )

            return HistoryData(
                ticker=symbol,
                period=period,
                interval=yf_interval,
                points=points,
                timestamp=datetime.now(UTC),
            )

        except TickerNotFoundError:
            raise
        except Exception as e:
            logger.error(f"yfinance history error for {symbol}: {e}")
            raise ExternalServiceError("yfinance", "Failed to fetch history data")

    def _get_mock_history(self, symbol: str, period: str) -> HistoryData:
        """Generate mock history data."""
        import random

        # Determine number of points based on period
        point_counts = {"1D": 78, "1W": 35, "1M": 22, "3M": 65, "6M": 130, "1Y": 252, "3Y": 756, "5Y": 260}
        num_points = point_counts.get(period, 22)

        yf_period, yf_interval = PERIOD_MAP.get(period, ("1mo", "1d"))

        # Generate price series with random walk
        base_price = random.uniform(100, 500)
        prices = [base_price]
        for _ in range(num_points - 1):
            change = random.gauss(0.0005, 0.02)
            prices.append(prices[-1] * (1 + change))

        # Generate points
        now = datetime.now(UTC)
        points: list[HistoryPoint] = []

        for i, price in enumerate(prices):
            days_back = num_points - i - 1
            date = now - timedelta(days=days_back)

            daily_vol = price * 0.02
            points.append(
                HistoryPoint(
                    date=date,
                    open=round(price - random.uniform(0, daily_vol), 2),
                    high=round(price + random.uniform(0, daily_vol), 2),
                    low=round(price - random.uniform(0, daily_vol), 2),
                    close=round(price, 2),
                    volume=random.randint(1_000_000, 50_000_000),
                )
            )

        return HistoryData(
            ticker=symbol,
            period=period,
            interval=yf_interval,
            points=points,
            timestamp=datetime.now(UTC),
        )


