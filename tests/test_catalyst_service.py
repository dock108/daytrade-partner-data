"""Tests for catalyst calendar service."""

import asyncio
from datetime import datetime, timezone

from app.models.catalyst import CatalystEvent
from app.services.catalyst_service import CatalystService


def test_catalyst_service_returns_events():
    service = CatalystService()
    events = asyncio.run(service.get_catalysts())

    assert events
    assert all(isinstance(event, CatalystEvent) for event in events)
    assert {event.type for event in events}
    assert {event.confidence for event in events}


def test_catalyst_service_caches_daily_snapshot():
    service = CatalystService()
    first = asyncio.run(service.get_catalysts())
    second = asyncio.run(service.get_catalysts())

    assert first is second


def test_catalyst_events_have_future_dates():
    service = CatalystService()
    events = asyncio.run(service.get_catalysts())
    now = datetime.now(timezone.utc)

    assert all(event.date >= now for event in events)


def test_catalyst_events_are_sorted_chronologically():
    service = CatalystService()
    events = asyncio.run(service.get_catalysts())

    dates = [event.date for event in events]
    assert dates == sorted(dates)
