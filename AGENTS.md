# AGENTS.md — TradeLens Backend (daytrade-partner-data)

> This file provides context for AI agents (Codex, Cursor, Copilot) working on this codebase.

## Quick Context

**What is this?** Python FastAPI backend for the TradeLens iOS trading companion app.

**Purpose:** Single source of truth for all market data consumed by the iOS app. The iOS app makes no direct external API calls.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, yfinance, OpenAI

**Key Directories:**
- `app/api/` — HTTP routers (endpoints)
- `app/services/` — Business logic
- `app/providers/` — Canonical data sources (single source of truth)
- `app/models/` — Pydantic request/response schemas
- `app/core/` — Config, logging, error handling
- `tests/` — Test suite

## Architecture

```
iOS App → API Layer → Services → Providers → External APIs
                                     ↓
                                  Cache
```

**Key principle:** All market data comes from `app/providers/`. Services and endpoints must NOT access yfinance or external APIs directly.

## File Organization

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP routing, request/response handling |
| `services/` | Business logic, data transformation |
| `providers/` | Data access, caching, external API calls |
| `models/` | Pydantic schemas (validation, serialization) |
| `core/` | Cross-cutting concerns (config, errors) |

## Coding Standards

1. **Async-first** — All service/provider methods should be `async`
2. **Type hints everywhere** — Use Python 3.11+ typing syntax
3. **Pydantic for validation** — Don't manually validate inputs
4. **Use providers** — Never import yfinance directly outside `app/providers/`
5. **Mock implementations** — Every service should work without external APIs
6. **100-char line limit** — See pyproject.toml

## Do NOT

- Add dependencies without justification
- Put business logic in routers (delegate to services)
- Use blocking I/O in async functions
- Access yfinance or external APIs outside providers
- Hardcode configuration (use `app/core/config.py`)
- Skip type hints

## iOS Model Alignment

Backend models must align with iOS Swift structs:

| Backend | iOS | Location |
|---------|-----|----------|
| `TickerSnapshot` | `TickerInfo` | `TradeLens/Models/TickerInfo.swift` |
| `PriceHistory` | `PriceHistory` | `TradeLens/Models/PriceData.swift` |
| `Outlook` | `Outlook` | `TradeLens/Models/Outlook.swift` |
| `AIResponse` | `AIResponse` | `TradeLens/Models/AIResponse.swift` |

## Required Response Fields

Every API response must include:
- `timestamp` — When data was fetched
- `source` — Data origin (`yfinance`, `openai`, `mock`)

## Testing

```bash
pytest tests/ -v
```

- Tests run in mock mode by default
- Add tests for new endpoints
- Use `pytest-asyncio` for async tests

## Running Locally

```bash
# Mock mode (default)
uvicorn app.main:app --reload

# Live mode
USE_MOCK_DATA=false uvicorn app.main:app --reload
```

## Getting Help

If something is unclear, add a `# TODO:` comment rather than guessing.
