# AGENTS.md — TradeLens Backend (daytrade-partner-data)

> This file provides context for AI agents (Codex, Cursor, Copilot) working on this codebase.

## Quick Context

**What is this?** Python FastAPI backend for the TradeLens iOS trading companion app.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, yfinance, OpenAI

**Key Directories:**
- `app/api/` — HTTP routers (endpoints)
- `app/services/` — Business logic
- `app/models/` — Pydantic request/response schemas
- `app/core/` — Config, logging, error handling
- `tests/` — Test suite

## Architecture

This backend is the **single source of truth** for data in the TradeLens ecosystem:
- iOS app (`daytrade-partner`) talks ONLY to this backend
- All external APIs (yfinance, OpenAI) are called from here
- Models here define the authoritative schemas

## Coding Standards

1. **Async-first** — All service methods should be `async`
2. **Type hints everywhere** — Use Python 3.11+ typing syntax
3. **Pydantic for validation** — Don't manually validate inputs
4. **Mock implementations** — Every service should work without external APIs
5. **100-char line limit** — See pyproject.toml

## File Organization

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP routing, request/response handling |
| `services/` | Business logic, external API calls |
| `models/` | Pydantic schemas (validation, serialization) |
| `core/` | Cross-cutting concerns (config, errors) |

## Do NOT

- Add dependencies without justification
- Put business logic in routers (delegate to services)
- Use blocking I/O in async functions
- Hardcode configuration (use `app/core/config.py`)
- Skip type hints

## iOS Model Alignment

Backend models must align with iOS Swift structs:

| Backend | iOS | Location |
|---------|-----|----------|
| `TickerSnapshot` | `TickerInfo` | `TradeLens/Models/TickerInfo.swift` |
| `PriceHistory` | `PriceHistory` | `TradeLens/Models/PriceData.swift` |
| `Outlook` | `Outlook` | `TradeLens/Services/OutlookEngine.swift` |
| `ExplainResponse` | `AIResponse` | `TradeLens/Models/AIResponse.swift` |

## Testing

- Add tests for new endpoints
- Use `pytest-asyncio` for async tests
- Mock external services in tests

```bash
pytest tests/ -v
```

## Running Locally

```bash
python main.py
# Or: uvicorn main:app --reload
```

## Getting Help

If something is unclear, add a `# TODO:` comment rather than guessing.

