# Data Contracts — Canonical Providers

> Single source of truth for all market data in TradeLens.

## Overview

All external data in the application flows through **canonical providers** in `app/providers/`. This architecture ensures:

- ✅ Consistent data shapes across all endpoints
- ✅ Unified caching with appropriate TTLs
- ✅ Timestamps and source attribution on all data
- ✅ No duplicate fetch logic
- ✅ Easy testing and mocking

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       API Endpoints                         │
│           /ticker, /outlook, /explain, etc.                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       Services                              │
│      TickerService, OutlookEngine, AIService               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Canonical Providers (Single Source)           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │PriceProvider│  │HistoryProv │  │ NewsProvider│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          │                                  │
│                    ┌─────▼─────┐                           │
│                    │   Cache   │                           │
│                    └───────────┘                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                 External APIs (yfinance, OpenAI)
```

---

## Providers

### PriceProvider

**Location:** `app/providers/price_provider.py`

**Function:** `async get_price(symbol: str) -> PriceData`

**Cache TTL:** 30 seconds

**Response Schema:**

```python
@dataclass
class PriceData:
    ticker: str              # "AAPL"
    current_price: float     # 185.50
    previous_close: float    # 183.25
    change: float            # 2.25
    change_percent: float    # 1.23
    day_high: float          # 186.20
    day_low: float           # 184.10
    week_52_high: float      # 199.62
    week_52_low: float       # 164.08
    volume: int              # 45000000
    market_cap: int | None   # 2890000000000
    timestamp: datetime      # 2024-01-15T10:30:00Z
    source: str              # "yfinance"
```

---

### HistoryProvider

**Location:** `app/providers/history_provider.py`

**Function:** `async get_history(symbol: str, period: str) -> HistoryData`

**Cache TTL:** 1 hour

**Supported Periods:** `1D`, `1W`, `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y`

**Response Schema:**

```python
@dataclass
class HistoryPoint:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class HistoryData:
    ticker: str                    # "AAPL"
    period: str                    # "1M"
    interval: str                  # "1d"
    points: list[HistoryPoint]     # OHLCV data
    timestamp: datetime            # When fetched
    source: str                    # "yfinance"
    
    # Computed properties
    start_price: float             # First close
    end_price: float               # Last close
    change: float                  # end - start
    change_percent: float          # % change
    closes: np.ndarray             # Close prices array
```

---

### NewsProvider

**Location:** `app/providers/news_provider.py`

**Function:** `async get_news(symbol: str | None, limit: int) -> NewsData`

**Cache TTL:** 6 hours

**Status:** Currently returns mock data. Real news API integration planned.

**Response Schema:**

```python
@dataclass
class NewsItem:
    title: str
    summary: str
    source: str           # "Reuters", "Bloomberg", etc.
    published_at: datetime
    url: str | None
    sentiment: str | None # "positive", "negative", "neutral"

@dataclass
class NewsData:
    ticker: str | None           # None for general market news
    items: list[NewsItem]
    timestamp: datetime
    source: str                  # "mock" (will change with real API)
```

---

## Cache Configuration

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Prices | 30 seconds | Near real-time, changes frequently |
| History | 1 hour | Daily data, rarely changes intraday |
| News | 6 hours | Updated periodically |

**Cache API:**

```python
from app.providers import cache

# Generic
cache.set("key", value, ttl=60)
cache.get("key")

# Convenience methods
cache.set_price("AAPL", data)
cache.get_price("AAPL")

cache.set_history("AAPL", "1M", data)
cache.get_history("AAPL", "1M")

cache.set_news(data, symbol="AAPL")
cache.get_news("AAPL")

# Stats
cache.stats  # {"size": 10, "hits": 10, "misses": 5, "hit_rate": 0.67}
```

---

## Usage Rules

### ✅ DO

```python
# Use providers in services
from app.providers import PriceProvider, HistoryProvider

class MyService:
    def __init__(self):
        self._price_provider = PriceProvider()
    
    async def get_data(self, symbol: str):
        return await self._price_provider.get_price(symbol)
```

### ❌ DON'T

```python
# Direct yfinance access is PROHIBITED outside providers
import yfinance as yf  # ❌ Wrong!

ticker = yf.Ticker("AAPL")  # ❌ Bypasses caching, validation
```

---

## Required Fields

Every provider response MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | datetime | When data was fetched |
| `source` | str | Data source identifier |

These fields enable:
- Cache invalidation
- Debugging data freshness
- Audit trails

---

## Testing

Tests verify:

1. **All services use providers** — No direct API access
2. **Timestamps exist** — Every response has `timestamp`
3. **Sources exist** — Every response has `source`
4. **Schemas match** — Correct field names and types

Run tests:

```bash
pytest tests/test_providers.py -v
```

---

## Mock vs Live Mode

| Mode | `USE_MOCK_DATA` | Provider Behavior |
|------|-----------------|-------------------|
| Mock | `true` (default) | Returns deterministic mock data |
| Live | `false` | Fetches from yfinance/real APIs |

Mock mode is always used for tests. Live mode requires network access.

---

## Adding New Providers

1. Create `app/providers/new_provider.py`
2. Define `@dataclass` for response with `timestamp` and `source`
3. Implement provider class with `async def get_*()` method
4. Add caching with appropriate TTL
5. Export from `app/providers/__init__.py`
6. Add tests in `tests/test_providers.py`
7. Update this document
