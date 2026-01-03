# TradeLens Backend — Project Guide

## Project Structure

```
daytrade-partner-data/
├── main.py                    # Entry point
├── pyproject.toml             # Dependencies
├── .env                       # Environment variables (not committed)
│
├── app/
│   ├── main.py                # FastAPI app factory
│   ├── api/                   # HTTP routers
│   │   ├── health.py          # GET /health
│   │   ├── market.py          # GET /ticker/{symbol}/*
│   │   ├── outlook.py         # POST /outlook
│   │   └── ai.py              # POST /explain
│   │
│   ├── services/              # Business logic
│   │   ├── ticker_service.py  # yfinance integration
│   │   ├── outlook_engine.py  # Statistical outlook computation
│   │   └── ai_service.py      # OpenAI integration
│   │
│   ├── models/                # Pydantic schemas
│   │   ├── ticker.py          # TickerSnapshot, PriceHistory
│   │   ├── outlook.py         # Outlook, OutlookRequest
│   │   └── explain.py         # AIResponse, ExplainRequest
│   │
│   └── core/                  # Cross-cutting concerns
│       ├── config.py          # Environment settings
│       ├── logging.py         # Logging setup
│       └── errors.py          # Custom exceptions
│
├── tests/                     # Test suite (49 tests)
│
└── docs/                      # Documentation
    ├── AGENTS.md              # AI coding assistant context
    ├── PROJECT_GUIDE.md       # This file
    └── API_CONTRACT.md        # API specification
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   TradeLens iOS App                         │
│                   (daytrade-partner)                        │
│                                                             │
│  • SwiftUI views and ViewModels                             │
│  • Local persistence (preferences, history)                 │
│  • Talks ONLY to this backend for data                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/JSON
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   TradeLens Backend                         │
│                   (this repo)                               │
│                                                             │
│  • Market data via yfinance                                 │
│  • Statistical outlooks (hit rate, volatility)              │
│  • AI explanations via OpenAI                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                 External Services
                 (Yahoo Finance, OpenAI)
```

### Design Principles

1. **iOS app has no direct external API access** — All data flows through this backend
2. **Backend owns the data contracts** — Pydantic models define schemas; iOS mirrors them
3. **Mock-first development** — All services work without external APIs
4. **No financial advice** — All outputs are descriptive, never predictive

## Layers

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP routing, validation, response formatting |
| `services/` | Business logic, external API calls |
| `models/` | Pydantic schemas with validation |
| `core/` | Config, logging, error handling |

## Code Style

- **Python 3.11+** with type hints everywhere
- **100-character line limit**
- **Async-first**: All service methods are `async`
- **Pydantic v2**: Use `model_config = ConfigDict(...)` not `class Config`

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `ticker_service.py` |
| Classes | PascalCase | `TickerService` |
| Functions | snake_case | `get_snapshot()` |
| Constants | UPPER_SNAKE | `DEFAULT_TIMEFRAME` |

## Adding New Endpoints

1. Create/update Pydantic model in `app/models/`
2. Add service method in `app/services/`
3. Create router in `app/api/`
4. Register router in `app/main.py`
5. Update `docs/API_CONTRACT.md`
6. Add tests in `tests/`

## Running Locally

```bash
# Install
pip install -e ".[dev]"

# Run
uvicorn app.main:app --reload

# Test
pytest tests/ -v
```

## Environment Variables

```env
USE_MOCK_DATA=true          # Mock data (default: true)
OPENAI_API_KEY=sk-...       # For AI explanations
DEBUG=true                  # Debug mode
```

## iOS Model Alignment

| Backend Model | iOS Struct |
|---------------|------------|
| `TickerSnapshot` | `TickerInfo` |
| `PriceHistory` | `PriceHistory` |
| `Outlook` | `Outlook` |
| `AIResponse` | `AIResponse` |
