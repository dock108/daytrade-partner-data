"""
Tests for PatternEngine core computations.
"""

from datetime import UTC, datetime

import numpy as np

from app.providers.history_provider import HistoryPoint
from app.services.pattern_engine import PatternEngine


def _make_point(day: int, close: float, high: float, low: float) -> HistoryPoint:
    return HistoryPoint(
        date=datetime(2024, 1, day, tzinfo=UTC),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=1_000_000,
    )


def test_compute_window_metrics():
    engine = PatternEngine()
    points = [
        _make_point(1, 100.0, 102.0, 98.0),
        _make_point(2, 105.0, 106.0, 101.0),
        _make_point(3, 110.0, 112.0, 104.0),
        _make_point(4, 100.0, 101.0, 95.0),
        _make_point(5, 95.0, 97.0, 90.0),
    ]

    returns, ranges = engine._compute_window_metrics(points, window_size=3)

    assert len(returns) == 3
    np.testing.assert_almost_equal(returns[0], 0.10, decimal=2)
    np.testing.assert_almost_equal(returns[1], -0.05, decimal=2)

    assert len(ranges) == 3
    np.testing.assert_almost_equal(ranges[0], 0.14, decimal=2)
    np.testing.assert_almost_equal(ranges[1], 0.16, decimal=2)


def test_matches_context_earnings_month():
    engine = PatternEngine()
    date = datetime(2024, 1, 15, tzinfo=UTC)

    assert engine._matches_context(date, ["earnings"])
    assert engine._matches_context(date, ["earnings", "fed week"])
    assert not engine._matches_context(date, ["high inflation"])
