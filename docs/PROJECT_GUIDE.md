# TradeLens Backend — Project Guide

## Overview

This repository is the **single source of truth** for all market data consumed by the TradeLens iOS app. The iOS app makes no direct external API calls — everything flows through this FastAPI backend.

---

## Project Structure

```
daytrade-partner-data/
├── main.py                    # Entry point (forwards to app.main)
├── pyproject.toml             # Dependencies
├── AGENTS.md                  # AI coding assistant context
├── .env                       # Environment variables (not committed)
│
├── app/
│   ├── main.py                # FastAPI app factory
│   │
│   ├── api/                   # HTTP routers
│   │   ├── health.py          # GET /health
│   │   ├── market.py          # GET /ticker/{symbol}/*
│   │   ├── outlook.py         # GET /outlook
│   │   └── ai.py              # POST /explain
│   │
│   ├── services/              # Business logic
│   │   ├── ticker_service.py  # Ticker data facade
│   │   ├── outlook_engine.py  # Statistical outlook computation
│   │   └── ai_service.py      # OpenAI integration
│   │
│   ├── providers/             # Canonical data sources (single source of truth)
│   │   ├── price_provider.py  # Current price data
│   │   ├── history_provider.py# Historical OHLCV data
│   │   ├── news_provider.py   # Market news (placeholder)
│   │   ├── cache.py           # Unified caching layer
│   │   └── guards.py          # Access safeguards
│   │
│   ├── models/                # Pydantic schemas
│   │   ├── ticker.py          # TickerSnapshot, PriceHistory
│   │   ├── outlook.py         # Outlook, OutlookRequest
│   │   ├── ai.py              # AIResponse
│   │   └── explain.py         # ExplainRequest
│   │
│   └── core/                  # Cross-cutting concerns
│       ├── config.py          # Environment settings
│       ├── logging.py         # Logging setup
│       └── errors.py          # Custom exceptions
│
├── tests/                     # Test suite
│
└── docs/                      # Documentation
    ├── PROJECT_GUIDE.md       # This file
    ├── API_CONTRACT.md        # API specification
    └── data-contracts.md      # Canonical provider specs
```

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
│         health.py │ market.py │ outlook.py │ ai.py          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                Services Layer (app/services/)               │
│     ticker_service.py │ outlook_engine.py │ ai_service.py   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Providers Layer (app/providers/)                 │
│   price_provider.py │ history_provider.py │ cache.py        │
│                  (Single Source of Truth)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                 External Services
                 (Yahoo Finance, OpenAI)
```

---

## Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP routing, validation, response formatting |
| `services/` | Business logic, data transformation, orchestration |
| `providers/` | Data access, caching, external API calls |
| `models/` | Pydantic schemas with validation |
| `core/` | Config, logging, error handling |

---

## Design Principles

1. **iOS app has no direct external API access** — All data flows through this backend
2. **Backend owns the data contracts** — Pydantic models define schemas; iOS mirrors them
3. **Canonical providers** — All market data comes from `app/providers/` (single source of truth)
4. **Mock-first development** — All services work without external APIs
5. **No financial advice** — All outputs are descriptive, never predictive

---

## Code Style

- **Python 3.11+** with type hints everywhere
- **100-character line limit**
- **Async-first**: All service/provider methods are `async`
- **Pydantic v2**: Use `model_config = ConfigDict(...)` not `class Config`

---

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `ticker_service.py` |
| Classes | PascalCase | `TickerService` |
| Functions | snake_case | `get_snapshot()` |
| Constants | UPPER_SNAKE | `DEFAULT_TIMEFRAME` |

---

## Adding New Endpoints

1. Create/update Pydantic model in `app/models/`
2. Add provider if new data source needed in `app/providers/`
3. Add service method in `app/services/`
4. Create router in `app/api/`
5. Register router in `app/main.py`
6. Update `docs/API_CONTRACT.md`
7. Add tests in `tests/`

---

## Running Locally

```bash
# Install
pip install -e ".[dev]"

# Run (mock mode)
uvicorn app.main:app --reload

# Run (live mode with real APIs)
USE_MOCK_DATA=false uvicorn app.main:app --reload

# Test
pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_DATA` | `true` | Mock data (default: true) |
| `OPENAI_API_KEY` | `""` | For AI explanations |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use |
| `DEBUG` | `false` | Debug mode |

Copy `.env.example` to `.env` and set values as needed.

---

## iOS Model Alignment

| Backend Model | iOS Struct |
|---------------|------------|
| `TickerSnapshot` | `TickerInfo` |
| `PriceHistory` | `PriceHistory` |
| `Outlook` | `Outlook` |
| `AIResponse` | `AIResponse` |

iOS decodes with `keyDecodingStrategy = .convertFromSnakeCase`.
