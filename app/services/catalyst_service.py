"""
Catalyst calendar service.

Provides upcoming macro and company-specific catalysts with daily caching.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.models.catalyst import CatalystEvent, CatalystType, ConfidenceLevel

logger = get_logger(__name__)

_CACHE_DATE: datetime | None = None
_CACHED_EVENTS: list[CatalystEvent] | None = None
_CACHE_TIMESTAMP: datetime | None = None

SOURCE = "mock"


@dataclass(frozen=True)
class CatalystSnapshot:
    """Snapshot of catalyst data with metadata."""

    events: list[CatalystEvent]
    timestamp: datetime
    source: str = SOURCE


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
        snapshot = await self.get_catalyst_snapshot()
        return snapshot.events

    async def get_catalyst_snapshot(self) -> CatalystSnapshot:
        global _CACHE_DATE, _CACHED_EVENTS, _CACHE_TIMESTAMP

        today = _utc_today()
        if _CACHE_DATE == today and _CACHED_EVENTS is not None and _CACHE_TIMESTAMP:
            logger.info("Returning cached catalyst calendar")
            return CatalystSnapshot(events=_CACHED_EVENTS, timestamp=_CACHE_TIMESTAMP)

        logger.info("Generating catalyst calendar snapshot")
        now = datetime.now(timezone.utc)
        events = _generate_mock_events(now)
        _CACHE_DATE = today
        _CACHED_EVENTS = events
        _CACHE_TIMESTAMP = now
        return CatalystSnapshot(events=events, timestamp=now)
