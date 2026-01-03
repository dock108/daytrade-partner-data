"""
Historical behavior pattern engine.

Computes descriptive statistics for historical windows that share
similar contextual conditions (earnings periods, Fed weeks, inflation regimes).
All outputs are descriptive — no predictions or financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from app.core.errors import TickerNotFoundError
from app.core.logging import get_logger
from app.models.pattern import BehaviorPattern
from app.providers.history_provider import HistoryPoint, HistoryProvider

logger = get_logger(__name__)

_CONTEXT_SYNONYMS: dict[str, str] = {
    "earnings": "earnings",
    "earnings period": "earnings",
    "earnings week": "earnings",
    "fed": "fed week",
    "fed week": "fed week",
    "fomc": "fed week",
    "high inflation": "high inflation",
    "inflation": "high inflation",
    "cpi": "high inflation",
}


class PatternEngine:
    """Engine for descriptive historical behavior patterns."""

    def __init__(self) -> None:
        self._history_provider = HistoryProvider()

    async def compute_pattern(self, symbol: str, context: list[str]) -> BehaviorPattern:
        """
        Compute descriptive statistics for historical periods sharing similar context.

        Args:
            symbol: Stock/ETF ticker symbol.
            context: Context tags (earnings period, high inflation, Fed week, etc.)

        Returns:
            BehaviorPattern summary.
        """
        snapshot = await self.compute_pattern_snapshot(symbol, context)
        return snapshot.pattern

    async def compute_pattern_snapshot(self, symbol: str, context: list[str]) -> "PatternSnapshot":
        """Compute behavior pattern with source metadata."""
        symbol = symbol.upper()
        logger.info("Computing behavior pattern for %s", symbol)

        history = await self._history_provider.get_history(symbol, "5Y", use_cache=True)
        if len(history.points) < 6:
            raise TickerNotFoundError(symbol)

        pattern = self._build_pattern(history.points, context)
        return PatternSnapshot(
            pattern=pattern,
            timestamp=history.timestamp,
            source=history.source,
        )

    def _compute_window_metrics(
        self,
        points: list[HistoryPoint],
        window_size: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute window returns and swing ranges for all rolling windows."""
        window_count = len(points) - window_size + 1
        if window_count <= 0:
            return np.array([]), np.array([])

        returns: list[float] = []
        ranges: list[float] = []

        for idx in range(window_count):
            window = points[idx : idx + window_size]
            start_price = window[0].close
            end_price = window[-1].close
            max_high = max(point.high for point in window)
            min_low = min(point.low for point in window)

            if start_price == 0:
                returns.append(0.0)
                ranges.append(0.0)
                continue

            returns.append((end_price - start_price) / start_price)
            ranges.append((max_high - min_low) / start_price)

        return np.array(returns), np.array(ranges)

    def _build_pattern(self, points: list[HistoryPoint], context: list[str]) -> BehaviorPattern:
        window_size = 5
        returns, ranges = self._compute_window_metrics(points, window_size)
        indices = self._select_window_indices(points, window_size, context)

        note = self._build_notes(context, filtered=True)
        if not indices:
            indices = list(range(len(returns)))
            note = self._build_notes(context, filtered=False)

        selected_returns = returns[indices]
        selected_ranges = ranges[indices]

        sample_size = int(len(selected_returns))
        win_rate = float(np.mean(selected_returns > 0)) if sample_size else 0.0
        typical_range = float(np.median(selected_ranges)) if sample_size else 0.0
        max_move = float(np.max(np.abs(selected_returns))) if sample_size else 0.0

        return BehaviorPattern(
            sample_size=sample_size,
            win_rate=round(win_rate, 2),
            typical_range=round(typical_range, 4),
            max_move=round(max_move, 4),
            notes=note,
        )

    def _select_window_indices(
        self,
        points: list[HistoryPoint],
        window_size: int,
        context: list[str],
    ) -> list[int]:
        """Select window indices whose start dates match all recognized context tags."""
        normalized = self._normalize_context(context)
        if not normalized:
            return list(range(len(points) - window_size + 1))

        indices: list[int] = []
        for idx in range(len(points) - window_size + 1):
            start_date = points[idx].date
            if self._matches_context(start_date, normalized):
                indices.append(idx)
        return indices

    def _matches_context(self, date: datetime, context: list[str]) -> bool:
        """Return True if date matches all recognized context tags."""
        matchers = [self._context_matcher(tag) for tag in context]
        matchers = [matcher for matcher in matchers if matcher is not None]
        if not matchers:
            return True
        return all(matcher(date) for matcher in matchers)

    def _context_matcher(self, tag: str):
        normalized = _CONTEXT_SYNONYMS.get(tag, tag)
        if normalized == "earnings":
            return lambda date: date.month in {1, 4, 7, 10}
        if normalized == "fed week":
            return lambda date: date.month in {1, 3, 5, 6, 7, 9, 11, 12}
        if normalized == "high inflation":
            return lambda date: date.year in {2021, 2022}
        return None

    def _normalize_context(self, context: list[str]) -> list[str]:
        normalized = []
        for raw in context:
            cleaned = raw.strip().lower()
            if not cleaned:
                continue
            normalized.append(_CONTEXT_SYNONYMS.get(cleaned, cleaned))
        return sorted(set(normalized))

    def _build_notes(self, context: list[str], filtered: bool) -> str:
        normalized = self._normalize_context(context)
        if not normalized:
            return "Behavior summarized across broader historical windows."

        readable = ", ".join(normalized)
        if filtered:
            return (
                f"Behavior clustered around {readable} windows; descriptive context only."
            )
        return (
            f"No direct matches for {readable}; using broader history for context only."
        )


@dataclass(frozen=True)
class PatternSnapshot:
    """Pattern analysis result with metadata."""

    pattern: BehaviorPattern
    timestamp: datetime
    source: str
