"""
Catalyst calendar service.

Provides upcoming macro and company-specific catalysts with daily caching.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.models.catalyst import CatalystEvent, CatalystType, ConfidenceLevel

logger = get_logger(__name__)

_CACHE_DATE: datetime | None = None
_CACHED_EVENTS: list[CatalystEvent] | None = None


def _utc_today() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _generate_mock_events(now: datetime) -> list[CatalystEvent]:
    base = now.replace(hour=13, minute=0, second=0, microsecond=0)
    return [
        CatalystEvent(
            type=CatalystType.EARNINGS,
            ticker="UNH",
            date=base + timedelta(days=1),
            confidence=ConfidenceLevel.HIGH,
        ),
        CatalystEvent(
            type=CatalystType.DIVIDEND,
            ticker="AAPL",
            date=base + timedelta(days=2),
            confidence=ConfidenceLevel.MEDIUM,
        ),
        CatalystEvent(
            type=CatalystType.SPLIT,
            ticker="NVDA",
            date=base + timedelta(days=5),
            confidence=ConfidenceLevel.MEDIUM,
        ),
        CatalystEvent(
            type=CatalystType.FED_MEETING,
            ticker=None,
            date=base + timedelta(days=9),
            confidence=ConfidenceLevel.HIGH,
        ),
        CatalystEvent(
            type=CatalystType.CPI,
            ticker=None,
            date=base + timedelta(days=12),
            confidence=ConfidenceLevel.HIGH,
        ),
        CatalystEvent(
            type=CatalystType.PPI,
            ticker=None,
            date=base + timedelta(days=13),
            confidence=ConfidenceLevel.MEDIUM,
        ),
        CatalystEvent(
            type=CatalystType.SECTOR,
            ticker="XLK",
            date=base + timedelta(days=4),
            confidence=ConfidenceLevel.MEDIUM,
        ),
    ]


class CatalystService:
    """Service providing upcoming catalyst calendar events."""

    async def get_catalysts(self) -> list[CatalystEvent]:
        global _CACHE_DATE, _CACHED_EVENTS

        today = _utc_today()
        if _CACHE_DATE == today and _CACHED_EVENTS is not None:
            logger.info("Returning cached catalyst calendar")
            return _CACHED_EVENTS

        logger.info("Generating catalyst calendar snapshot")
        now = datetime.now(timezone.utc)
        events = _generate_mock_events(now)
        _CACHE_DATE = today
        _CACHED_EVENTS = events
        return events
