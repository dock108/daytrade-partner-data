"""
Canonical data providers — single source of truth for all market data.

All API endpoints and services MUST use these providers for data access.
Direct yfinance or external API calls outside these providers are prohibited.
"""

from app.providers.cache import cache
from app.providers.guards import (
    DirectAPIAccessError,
    guard_direct_access,
    validate_provider_response,
)
from app.providers.history_provider import HistoryData, HistoryPoint, HistoryProvider
from app.providers.news_provider import NewsData, NewsItem, NewsProvider
from app.providers.price_provider import PriceData, PriceProvider

__all__ = [
    # Providers
    "PriceProvider",
    "HistoryProvider",
    "NewsProvider",
    # Data classes
    "PriceData",
    "HistoryData",
    "HistoryPoint",
    "NewsData",
    "NewsItem",
    # Cache
    "cache",
    # Guards
    "DirectAPIAccessError",
    "guard_direct_access",
    "validate_provider_response",
]

