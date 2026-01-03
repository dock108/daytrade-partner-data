# TradeLens Backend — Project Guide

## Project Structure

The project follows a clean layered architecture with clear separation of concerns:

```
daytrade-partner-data/
├── main.py                    # Application entry point
├── pyproject.toml             # Dependencies and project config
├── .env                       # Environment variables (not committed)
│
├── app/                       # Main application package
│   ├── __init__.py            # App factory
│   │
│   ├── api/                   # HTTP endpoints (routers)
│   │   ├── health.py          # Health check endpoint
│   │   ├── ticker.py          # Ticker snapshot & history
│   │   ├── outlook.py         # Market outlook generation
│   │   └── explain.py         # AI explanations
│   │
│   ├── services/              # Business logic layer
│   │   ├── ticker_service.py  # yfinance integration, price data
│   │   ├── outlook_service.py # Outlook synthesis engine
│   │   └── explain_service.py # OpenAI integration, AI responses
│   │
│   ├── models/                # Pydantic schemas
│   │   ├── ticker.py          # TickerSnapshot, PriceHistory
│   │   ├── outlook.py         # Outlook, SentimentSummary
│   │   └── explain.py         # ExplainRequest, ExplainResponse
│   │
│   └── core/                  # Cross-cutting concerns
│       ├── config.py          # Environment-based settings
│       ├── logging.py         # Logging configuration
│       └── errors.py          # Custom exceptions
│
├── tests/                     # Test suite
│   ├── test_health.py
│   └── test_ticker.py
│
└── docs/                      # Documentation
    ├── PROJECT_GUIDE.md       # This file
    └── API_CONTRACT.md        # HTTP API specification
```

## Architecture Overview

### Relationship to TradeLens iOS App

**This backend is the single source of truth** for data, statistics, and AI-generated explanations. The architecture enforces a clean separation:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TradeLens iOS App                           │
│  (daytrade-partner)                                             │
│                                                                 │
│  • SwiftUI views and ViewModels                                 │
│  • Local persistence (conversation history, preferences)        │
│  • Voice input and UI interactions                              │
│  • Talks ONLY to this backend for data                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/JSON
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TradeLens Backend API                         │
│  (daytrade-partner-data)                                        │
│                                                                 │
│  • Market data (yfinance)                                       │
│  • Outlook generation (sector trends, volatility)               │
│  • AI explanations (OpenAI)                                     │
│  • Future ML/analytics models                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     External Services       │
              │  • Yahoo Finance API        │
              │  • OpenAI API               │
              │  • (Future: ML models)      │
              └─────────────────────────────┘
```

### Design Principles

1. **iOS app has no direct external API access** — All market data and AI responses flow through this backend.
2. **Backend owns the data contracts** — Pydantic models here define the schemas; iOS models mirror them.
3. **Mock-first development** — Every service has mock implementations for offline development.
4. **No financial advice** — Outlooks and explanations are descriptive, never predictive.

### API Layer (`app/api/`)

HTTP routers using FastAPI. Each router:
- Handles request validation automatically (Pydantic)
- Returns typed response models
- Delegates to service layer for logic

### Services Layer (`app/services/`)

Business logic and external integrations. Services:
- Are stateless and async-first
- Have mock implementations for testing
- Handle external API errors gracefully

### Models Layer (`app/models/`)

Pydantic models for request/response schemas. Models:
- Align 1:1 with iOS Swift structs
- Include validation constraints
- Have example JSON for documentation

### Core Layer (`app/core/`)

Cross-cutting utilities:
- **config.py**: Environment-based settings via pydantic-settings
- **logging.py**: Structured logging
- **errors.py**: Custom HTTP exceptions

## Key Features

### Ticker Snapshot & History

Provides company information and price history for charting:
- Aligns with iOS `TickerInfo` and `PriceHistory` models
- Currently uses mock data; yfinance integration planned

### Outlook Engine

Synthesizes market data into structured outlooks:
- Generates `Outlook` objects with sentiment, drivers, volatility
- Mirrors iOS `OutlookEngine.swift` logic
- Descriptive metrics only — no predictions

### AI Explanations

Article-style responses to user queries:
- Structured into sections (current situation, key drivers, recap)
- Aligns with iOS `AIResponse` model
- OpenAI integration planned; currently mocked

## Development Guidelines

### Code Style

- **Python 3.11+** features encouraged (type hints, `|` union syntax)
- **100-character line limit** (see pyproject.toml)
- **Async-first**: All service methods are `async`
- **Type hints everywhere**: Pydantic + explicit return types

### File Organization

When a module exceeds ~300 lines:
1. Split into focused submodules
2. Re-export from `__init__.py`
3. Keep each file single-purpose

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `ticker_service.py` |
| Classes | PascalCase | `TickerService` |
| Functions | snake_case | `get_snapshot()` |
| Constants | UPPER_SNAKE | `DEFAULT_TIMEFRAME` |
| Pydantic models | PascalCase | `TickerSnapshot` |

### Adding New Endpoints

1. Create/update Pydantic model in `app/models/`
2. Add service method in `app/services/`
3. Create router in `app/api/`
4. Register router in `app/__init__.py`
5. Update `docs/API_CONTRACT.md`
6. Add tests in `tests/`

### Best Practices

1. **Separation of Concerns**: Routers validate, services compute
2. **Mock Everything**: Use `USE_MOCK_DATA` flag for development
3. **Explicit Errors**: Raise custom exceptions, not generic ones
4. **Document as You Go**: Keep API_CONTRACT.md current

## Requirements

- **Python**: 3.11+
- **Package Manager**: uv or pip
- **Framework**: FastAPI

## Running the Project

### Local Development

```bash
# Install dependencies (with uv)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Run development server
python main.py
# Or with uvicorn directly
uvicorn main:app --reload --port 8000
```

### Running Tests

```bash
pytest tests/ -v
```

### Environment Variables

Create a `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Feature Flags
USE_MOCK_DATA=true

# External Services (when ready)
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

## Contributing

When adding new features:
1. Place files in the appropriate folder based on responsibility
2. Follow existing naming patterns
3. Add Pydantic models with examples and validation
4. Write tests for new endpoints
5. Update API_CONTRACT.md with endpoint documentation
6. Keep functions focused and under 50 lines when possible

## Future Work

- [ ] yfinance integration for live market data
- [ ] OpenAI integration for AI explanations
- [ ] User context/trade history for personalized insights
- [ ] Caching layer for frequently requested data
- [ ] ML models for pattern recognition (sibling repo or submodule)

