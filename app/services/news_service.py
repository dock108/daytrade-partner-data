"""
News service — relevance-ranked headlines for tickers or sectors.

Transforms provider data into the API-facing response shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.logging import get_logger
from app.providers.news_provider import NewsItem, NewsProvider

logger = get_logger(__name__)

_KEYWORDS = [
    "earnings",
    "guidance",
    "downgrade",
    "lawsuit",
    "regulation",
    "supply chain",
    "margin",
    "cost",
    "demand",
    "layoffs",
    "options",
    "warning",
]

_PRIMARY_WINDOW_DAYS = 7
_MACRO_FALLBACK_MIN_DAYS = 30
_MACRO_FALLBACK_MAX_DAYS = 60


@dataclass(frozen=True)
class _QueryContext:
    ticker: str | None
    sector: str | None

    @property
    def macro_theme(self) -> bool:
        return self.ticker is None and self.sector is not None


class NewsService:
    """Service that returns relevance-ranked news with ticker/sector filtering."""

    def __init__(self, provider: NewsProvider | None = None) -> None:
        self._provider = provider or NewsProvider()

    async def get_news(
        self,
        ticker: str | None = None,
        sector: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get ranked news for a ticker or sector.

        Args:
            ticker: Ticker symbol (optional)
            sector: Sector name (optional)
            limit: Maximum number of articles to return
        """
        context = _QueryContext(
            ticker=ticker.upper() if ticker else None,
            sector=sector,
        )
        provider_symbol = context.ticker if context.ticker else None

        news = await self._provider.get_news(provider_symbol, limit=limit)
        items = self._filter_by_date(news.items, context)
        items = self._filter_by_sector(items, context)

        ranked = [
            self._format_item(item, context)
            for item in items
        ]
        ranked.sort(key=lambda item: (item["relevance"], item["published"]), reverse=True)

        return ranked[:limit]

    def _filter_by_date(self, items: list[NewsItem], context: _QueryContext) -> list[NewsItem]:
        now = datetime.now(UTC)
        recent_cutoff = now - timedelta(days=_PRIMARY_WINDOW_DAYS)
        recent_items = [item for item in items if item.published_at >= recent_cutoff]

        if recent_items or not context.macro_theme:
            return recent_items

        fallback_start = now - timedelta(days=_MACRO_FALLBACK_MAX_DAYS)
        fallback_end = now - timedelta(days=_MACRO_FALLBACK_MIN_DAYS)
        fallback_items = [
            item
            for item in items
            if fallback_start <= item.published_at <= fallback_end
        ]
        if fallback_items:
            logger.info("Using macro fallback window for news results.")
        return fallback_items

    def _filter_by_sector(self, items: list[NewsItem], context: _QueryContext) -> list[NewsItem]:
        if not context.sector:
            return items
        sector_lower = context.sector.lower()
        return [
            item
            for item in items
            if sector_lower in self._combined_text(item).lower()
        ]

    def _format_item(self, item: NewsItem, context: _QueryContext) -> dict:
        relevance = self._calculate_relevance(item, context)
        ticker_match = False
        if context.ticker:
            ticker_match = context.ticker.lower() in self._combined_text(item).lower()

        return {
            "headline": item.title,
            "summary": item.summary,
            "url": item.url,
            "published": item.published_at.isoformat(),
            "relevance": relevance,
            "ticker_match": ticker_match,
        }

    def _calculate_relevance(self, item: NewsItem, context: _QueryContext) -> float:
        title_lower = item.title.lower()
        summary_lower = item.summary.lower()
        combined_lower = f"{title_lower} {summary_lower}"

        title_hits = sum(1 for keyword in _KEYWORDS if keyword in title_lower)
        summary_hits = sum(1 for keyword in _KEYWORDS if keyword in summary_lower)
        combined_hits = sum(1 for keyword in _KEYWORDS if keyword in combined_lower)

        relevance = 0.1 * combined_hits + 0.15 * summary_hits + 0.2 * title_hits

        if context.ticker and context.ticker.lower() in combined_lower:
            relevance += 0.2
        if context.sector and context.sector.lower() in combined_lower:
            relevance += 0.1

        return min(relevance, 1.0)

    @staticmethod
    def _combined_text(item: NewsItem) -> str:
        return f"{item.title} {item.summary}"
