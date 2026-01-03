# daytrade-partner-data

Backend API and future ML layer for the **TradeLens** iOS trading companion app.

## Overview

This repository provides the data backend for the TradeLens iOS app. It serves as the single source of truth for market data, analytics, and AI-generated explanations.

## Architecture: Client ↔ Backend

```
┌────────────────────────────────────┐
│       daytrade-partner             │
│       (TradeLens iOS App)          │
│                                    │
│  • SwiftUI views and ViewModels    │
│  • Local storage (preferences,     │
│    conversation history)           │
│  • Voice input & UI                │
└─────────────┬──────────────────────┘
              │
              │  HTTP/JSON
              │  (all data requests)
              ▼
┌────────────────────────────────────┐
│     daytrade-partner-data          │
│     (This Repository)              │
│                                    │
│  • Market data (yfinance)          │
│  • Outlook generation              │
│  • AI explanations (OpenAI)        │
│  • Future ML/analytics models      │
└────────────────────────────────────┘
```

### Key Design Decisions

1. **iOS app talks ONLY to this backend** — No direct calls to Yahoo Finance, OpenAI, or other external APIs from the app.

2. **Backend owns the data contracts** — Pydantic models here define the authoritative schemas. iOS models mirror them.

3. **Mock-first development** — All services have mock implementations, enabling offline development and testing.

4. **No financial advice** — All outputs are descriptive metrics, never predictions or recommendations.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/daytrade-partner-data.git
cd daytrade-partner-data

# Install with uv
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Running the Server

```bash
# Development server with auto-reload
python main.py

# Or directly with uvicorn
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ticker/{symbol}/snapshot` | GET | Company info and metadata |
| `/ticker/{symbol}/history` | GET | Price history for charting |
| `/outlook` | GET | Structured market outlook |
| `/explain` | POST | AI-powered explanation |

See [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) for full endpoint documentation.

## Project Structure

```
daytrade-partner-data/
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies
├── app/
│   ├── api/                # HTTP routers
│   ├── services/           # Business logic
│   ├── models/             # Pydantic schemas
│   └── core/               # Config, logging, errors
├── tests/                  # Test suite
└── docs/
    ├── PROJECT_GUIDE.md    # Architecture guide
    └── API_CONTRACT.md     # API specification
```

## Configuration

Create a `.env` file:

```env
USE_MOCK_DATA=true          # Use mock data (default: true)
OPENAI_API_KEY=             # OpenAI API key (when ready)
DEBUG=true                  # Enable debug mode
```

## Testing

```bash
pytest tests/ -v
```

## Documentation

- [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) — Architecture, conventions, development guide
- [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) — Endpoint specifications and schemas

## Related Repositories

| Repository | Description |
|------------|-------------|
| [daytrade-partner](../daytrade-partner) | TradeLens iOS app (SwiftUI client) |
| daytrade-partner-data | This repo (FastAPI backend) |

---

Built with FastAPI + Python 3.11

