"""
Unified caching layer for data providers.

Cache TTLs:
- Prices: 15-30 seconds (real-time data)
- Historical: 1-6 hours (rarely changes)
- News: 6-12 hours (updated periodically)
"""

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """A cached value with expiration."""

    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class Cache:
    """
    Simple in-memory cache with TTL support.

    Thread-safe for single-threaded async usage.
    For production, consider Redis or similar.
    """

    # Default TTLs in seconds
    TTL_PRICE = 30  # 30 seconds for real-time prices
    TTL_HISTORY = 3600  # 1 hour for historical data
    TTL_NEWS = 21600  # 6 hours for news

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get a value from cache, returns None if expired or missing."""
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional TTL override."""
        ttl = ttl or self.TTL_PRICE
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + ttl,
        )

    def delete(self, key: str) -> None:
        """Remove a key from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired entries, return count removed."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
        }

    # Convenience methods for specific data types
    def get_price(self, symbol: str) -> Any | None:
        return self.get(f"price:{symbol.upper()}")

    def set_price(self, symbol: str, value: Any) -> None:
        self.set(f"price:{symbol.upper()}", value, self.TTL_PRICE)

    def get_history(self, symbol: str, period: str) -> Any | None:
        return self.get(f"history:{symbol.upper()}:{period}")

    def set_history(self, symbol: str, period: str, value: Any) -> None:
        self.set(f"history:{symbol.upper()}:{period}", value, self.TTL_HISTORY)

    def get_news(self, symbol: str | None = None) -> Any | None:
        key = f"news:{symbol.upper()}" if symbol else "news:market"
        return self.get(key)

    def set_news(self, value: Any, symbol: str | None = None) -> None:
        key = f"news:{symbol.upper()}" if symbol else "news:market"
        self.set(key, value, self.TTL_NEWS)


# Global cache instance
cache = Cache()

