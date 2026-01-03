"""
Outlook computation engine.

Computes descriptive statistics for a ticker over a given timeframe
using historical price data from canonical providers.
All outputs are descriptive — no predictions or financial advice.
"""

from datetime import UTC, datetime

import numpy as np

from app.core.errors import TickerNotFoundError
from app.core.logging import get_logger
from app.models.outlook import Outlook, SentimentSummary
from app.providers.history_provider import HistoryProvider

logger = get_logger(__name__)

# Placeholder key drivers — descriptive, not predictive
DEFAULT_KEY_DRIVERS = [
    "Company earnings and guidance",
    "Sector trends",
    "Broader market conditions",
]


def _classify_volatility(annualized_std: float) -> str:
    """
    Classify volatility based on annualized standard deviation.

    Buckets:
    - low: < 20% annualized
    - moderate: 20-40% annualized
    - high: > 40% annualized
    """
    if annualized_std < 0.20:
        return "low"
    elif annualized_std < 0.40:
        return "moderate"
    else:
        return "high"


def _determine_sentiment(
    hit_rate: float,
    recent_90d_return: float,
) -> SentimentSummary:
    """
    Determine sentiment from historical hit rate and recent 90-day trend.

    Logic:
    - positive: hit_rate > 55% AND recent return > 0
    - cautious: hit_rate < 45% OR recent return < -10%
    - mixed: everything else
    """
    if hit_rate > 0.55 and recent_90d_return > 0:
        return SentimentSummary.POSITIVE
    elif hit_rate < 0.45 or recent_90d_return < -0.10:
        return SentimentSummary.CAUTIOUS
    else:
        return SentimentSummary.MIXED


class OutlookEngine:
    """
    Engine for computing statistical outlooks from historical price data.

    All data comes from canonical HistoryProvider.
    Computations are based on historical data — no predictions or advice.
    """

    def __init__(self):
        self._history_provider = HistoryProvider()

    async def compute_outlook(
        self,
        symbol: str,
        timeframe_days: int = 30,
    ) -> Outlook:
        """
        Compute an outlook for a ticker based on historical price data.

        Args:
            symbol: Stock/ETF ticker symbol.
            timeframe_days: Window for rolling return analysis (10-365 days).

        Returns:
            Outlook with computed statistics.

        Raises:
            TickerNotFoundError: If ticker is not found.
            ExternalServiceError: If data provider fails.
        """
        symbol = symbol.upper()
        logger.info(f"Computing {timeframe_days}-day outlook for {symbol}")

        # Get 3 years of history from canonical provider
        history = await self._history_provider.get_history(symbol, "3Y", use_cache=True)

        if len(history.points) < timeframe_days + 1:
            raise TickerNotFoundError(symbol)

        # Extract close prices
        closes = history.closes

        # Compute rolling returns over timeframe_days windows
        rolling_returns = self._compute_rolling_returns(closes, timeframe_days)

        if len(rolling_returns) == 0:
            raise TickerNotFoundError(symbol)

        # Hit rate: fraction of windows with positive return
        hit_rate = float(np.mean(rolling_returns > 0))

        # Standard deviation of rolling returns
        rolling_std = float(np.std(rolling_returns))

        # Annualized standard deviation (for volatility classification)
        annualized_std = rolling_std * np.sqrt(252 / timeframe_days)

        # Typical range percent: 1 std dev magnitude as percentage
        typical_range_percent = rolling_std

        # Volatility label based on annualized std dev
        volatility_label = _classify_volatility(annualized_std)

        # Recent 90-day return for sentiment
        recent_90d_return = self._compute_recent_return(closes, 90)

        # Determine sentiment from hit rate + recent trend
        sentiment = _determine_sentiment(hit_rate, recent_90d_return)

        # Build key drivers (placeholder + context-aware entries)
        key_drivers = self._build_key_drivers(volatility_label, sentiment)

        return Outlook(
            ticker=symbol,
            timeframe_days=timeframe_days,
            sentiment_summary=sentiment,
            key_drivers=key_drivers,
            volatility_band=round(typical_range_percent, 4),
            historical_hit_rate=round(hit_rate, 2),
            personal_context=None,
            volatility_warning=self._get_volatility_warning(volatility_label),
            timeframe_note=None,
            generated_at=datetime.now(UTC),
        )

    def _compute_rolling_returns(
        self,
        closes: np.ndarray,
        window: int,
    ) -> np.ndarray:
        """
        Compute rolling returns over a given window.

        For each position i >= window, compute:
        return[i] = (closes[i] - closes[i-window]) / closes[i-window]
        """
        if len(closes) <= window:
            return np.array([])

        start_prices = closes[:-window]
        end_prices = closes[window:]

        returns = (end_prices - start_prices) / start_prices
        return returns

    def _compute_recent_return(
        self,
        closes: np.ndarray,
        days: int,
    ) -> float:
        """Compute return over the most recent N days."""
        if len(closes) < days + 1:
            days = len(closes) - 1

        if days <= 0:
            return 0.0

        start_price = closes[-(days + 1)]
        end_price = closes[-1]

        return float((end_price - start_price) / start_price)

    def _build_key_drivers(
        self,
        volatility_label: str,
        sentiment: SentimentSummary,
    ) -> list[str]:
        """Build list of key drivers based on current conditions."""
        drivers = list(DEFAULT_KEY_DRIVERS)

        # Add volatility-aware driver
        if volatility_label == "high":
            drivers.append("Elevated price swings observed in recent trading")
        elif volatility_label == "low":
            drivers.append("Relatively stable price action in recent history")

        # Add sentiment-aware driver
        if sentiment == SentimentSummary.POSITIVE:
            drivers.append("Historical patterns show above-average positive windows")
        elif sentiment == SentimentSummary.CAUTIOUS:
            drivers.append("Recent performance below historical averages")

        return drivers

    def _get_volatility_warning(self, volatility_label: str) -> str | None:
        """Return a warning if volatility is high."""
        if volatility_label == "high":
            return "This ticker has shown elevated volatility in recent history."
        return None
