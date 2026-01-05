# daytrade-partner-data

**Backend data layer for TradeLens** — the iOS trading companion app.

This repository is the **single source of truth** for all market data, statistical outlooks, and AI-powered explanations consumed by the TradeLens iOS app. The iOS app makes no direct external API calls; everything flows through this backend.

---

## What Lives Here

| Data Type | Description | Source |
|-----------|-------------|--------|
| **Price Data** | Real-time quotes, 52-week ranges, volume | yfinance |
| **Price History** | OHLCV data for charting (1D to 5Y) | yfinance |
| **Statistical Outlooks** | Hit rates, volatility bands, sentiment | Computed from history |
| **AI Explanations** | Contextual market commentary | OpenAI GPT |
| **News** | Market news headlines (placeholder) | Mock (API integration planned) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   TradeLens iOS App                         │
│                   (daytrade-partner)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/JSON
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Layer (app/api/)                      │
│     Endpoints: /health, /ticker, /outlook, /explain         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                Services Layer (app/services/)               │
│     Business logic, outlook computation, AI prompts         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Providers Layer (app/providers/)                 │
│     Canonical data sources with caching + timestamps        │
│              (Single Source of Truth)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                External APIs (Yahoo Finance, OpenAI)
```

---

## Data Modes

| Mode | `USE_MOCK_DATA` | Description |
|------|-----------------|-------------|
| **Mock** | `true` (default) | Uses built-in mock data. No external API calls. Fast, deterministic, works offline. |
| **Live** | `false` | Fetches real data from yfinance/OpenAI. Requires network + API keys. |

Mock mode is the default for local development and testing.

---

## Schemas

All data structures are defined as **Pydantic models** in `app/models/`. These models:

- Define the authoritative contract between backend and iOS
- Include validation, type hints, and JSON examples
- Serialize to JSON with `snake_case` (iOS uses `camelCase` decoder)

| Model | Purpose | Location |
|-------|---------|----------|
| `TickerSnapshot` | Company info, current price, 52-week range | `app/models/ticker.py` |
| `PriceHistory` | OHLCV chart data with change metrics | `app/models/ticker.py` |
| `Outlook` | Statistical outlook with hit rate, volatility | `app/models/outlook.py` |
| `AIResponse` | Structured AI explanation (5 fields) | `app/models/ai.py` |

Every API response includes:
- `timestamp` — when the data was fetched
- `source` — data origin (`yfinance`, `openai`, `mock`)

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/dock108/daytrade-partner-data.git
cd daytrade-partner-data
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run (mock mode - no API keys needed)
uvicorn app.main:app --reload --port 8000

# Verify
curl http://localhost:8000/health
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ticker/{symbol}/snapshot` | GET | Company info, price, 52-week range |
| `/ticker/{symbol}/history` | GET | Price history for charting |
| `/outlook` | GET | Statistical outlook (hit rate, volatility) |
| `/explain` | POST | AI-powered market explanation |

**Interactive docs**: http://localhost:8000/docs

---

## Example Requests

```bash
# Ticker snapshot
curl http://localhost:8000/ticker/AAPL/snapshot

# Price history (1 month)
curl "http://localhost:8000/ticker/NVDA/history?range=1M"

# Outlook
curl "http://localhost:8000/outlook?ticker=SPY&timeframe_days=30"

# AI Explanation
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"question": "What is happening with AAPL?", "symbol": "AAPL"}'
```

---

## Testing

```bash
pytest tests/ -v
```

Tests run in mock mode by default. The test suite covers:
- All API endpoints
- Provider data contracts (timestamps, sources)
- Service layer logic
- Edge cases and error handling

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_DATA` | `true` | Use mock data (no external APIs needed) |
| `OPENAI_API_KEY` | `""` | OpenAI key for /explain endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `DEBUG` | `false` | Enable debug logging |

Copy `.env.example` to `.env` and set values as needed.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Endpoint specifications and response schemas |
| [docs/data-contracts.md](docs/data-contracts.md) | Canonical provider architecture |
| [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) | Development guide and architecture |
| [AGENTS.md](AGENTS.md) | Context for AI coding assistants |

---

## iOS Integration

This backend defines the **authoritative schemas**. The iOS app mirrors these models:

| Backend Model | iOS Struct |
|---------------|------------|
| `TickerSnapshot` | `TickerInfo` |
| `PriceHistory` | `PriceHistory` |
| `Outlook` | `Outlook` |
| `AIResponse` | `AIResponse` |

iOS decodes responses with:

```swift
let decoder = JSONDecoder()
decoder.keyDecodingStrategy = .convertFromSnakeCase
```

---

Built with **FastAPI + Python 3.11** • Data via **yfinance** • AI via **OpenAI**
