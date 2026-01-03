from __future__ import annotations

from asyncio import run
from datetime import UTC, datetime, timedelta

from app.providers.news_provider import NewsData, NewsItem
from app.services.news_service import NewsService


class _StubNewsProvider:
    def __init__(self, items: list[NewsItem]) -> None:
        self._items = items

    async def get_news(self, symbol: str | None = None, limit: int = 10) -> NewsData:
        return NewsData(
            ticker=symbol,
            items=self._items[:limit],
            timestamp=datetime.now(UTC),
        )


def test_get_news_rejects_items_older_than_60_days() -> None:
    now = datetime.now(UTC)
    stale_item = NewsItem(
        title="Older headline",
        summary="Old summary",
        source="Archive",
        published_at=now - timedelta(days=61),
        url=None,
        sentiment=None,
    )
    service = NewsService(provider=_StubNewsProvider([stale_item]))

    result = run(service.get_news(ticker="AAPL", limit=5))

    assert result == []


def test_macro_fallback_allows_30_to_60_day_window() -> None:
    now = datetime.now(UTC)
    fallback_item = NewsItem(
        title="Tech sector sees mixed demand",
        summary="Tech companies are adjusting to macro conditions.",
        source="MacroWire",
        published_at=now - timedelta(days=40),
        url=None,
        sentiment=None,
    )
    service = NewsService(provider=_StubNewsProvider([fallback_item]))

    result = run(service.get_news(sector="Tech", limit=5))

    assert len(result) == 1
    assert result[0]["headline"] == fallback_item.title


def test_get_news_filters_out_stale_items() -> None:
    now = datetime.now(UTC)
    fresh_item = NewsItem(
        title="Fresh headline",
        summary="Fresh summary",
        source="Wire",
        published_at=now - timedelta(days=3),
        url=None,
        sentiment=None,
    )
    stale_item = NewsItem(
        title="Stale headline",
        summary="Stale summary",
        source="Archive",
        published_at=now - timedelta(days=75),
        url=None,
        sentiment=None,
    )
    service = NewsService(provider=_StubNewsProvider([fresh_item, stale_item]))

    result = run(service.get_news(ticker="AAPL", limit=5))

    assert len(result) == 1
    assert result[0]["headline"] == fresh_item.title
    published = datetime.fromisoformat(result[0]["published"])
    assert published >= now - timedelta(days=60)
