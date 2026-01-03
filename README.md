# daytrade-partner-data

Backend API for the **TradeLens** iOS trading companion app.

Provides market data, statistical outlooks, and AI-powered explanations — all descriptive, never predictive.

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/dock108/daytrade-partner-data.git
cd daytrade-partner-data

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Feature flags
USE_MOCK_DATA=true          # Set to false to use live yfinance data

# OpenAI (optional - required for AI explanations)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Debug
DEBUG=true
```

> **Note**: With `USE_MOCK_DATA=true`, all endpoints work without external API keys.

### 3. Run the Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --port 8000

# Or use the entry point
python main.py
```

The API is now running at **http://localhost:8000**

### 4. Verify It Works

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## API Documentation

Once running, interactive docs are available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ticker/{symbol}/snapshot` | GET | Company info, price, 52-week range |
| `/ticker/{symbol}/history` | GET | Price history for charting |
| `/outlook` | POST | Statistical outlook with hit rate, volatility |
| `/explain` | POST | AI-powered market explanation |

---

## Example Requests

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok"}
```

---

### Ticker Snapshot

```bash
curl http://localhost:8000/ticker/AAPL/snapshot
```

**Response:**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "market_cap": "2.89T",
  "volatility": "low",
  "current_price": 185.50,
  "change_percent": 1.25,
  "week_52_high": 199.62,
  "week_52_low": 164.08
}
```

---

### Ticker History

```bash
curl "http://localhost:8000/ticker/NVDA/history?range=1M"
```

**Query Parameters:**
- `range`: `1D`, `1M`, `6M`, or `1Y` (default: `1M`)

**Response:**
```json
{
  "ticker": "NVDA",
  "points": [
    {"date": "2024-01-02T16:00:00Z", "close": 480.25, "high": 482.50, "low": 478.00},
    {"date": "2024-01-03T16:00:00Z", "close": 485.10, "high": 487.20, "low": 481.30}
  ],
  "current_price": 485.10,
  "change": 4.85,
  "change_percent": 1.01
}
```

---

### Outlook (Statistical Analysis)

```bash
curl -X POST http://localhost:8000/outlook \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "timeframeDays": 30}'
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "timeframeDays": 30
}
```

**Response:**
```json
{
  "ticker": "AAPL",
  "timeframe_days": 30,
  "sentiment_summary": "positive",
  "key_drivers": [
    "Company earnings and guidance",
    "Sector trends",
    "Broader market conditions"
  ],
  "volatility_band": 0.08,
  "historical_hit_rate": 0.64,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

---

### Explain (AI-Powered)

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is happening with NVDA today?",
    "symbol": "NVDA",
    "timeframeDays": 30,
    "simpleMode": false
  }'
```

**Request Body:**
```json
{
  "question": "What is happening with NVDA today?",
  "symbol": "NVDA",
  "timeframeDays": 30,
  "simpleMode": false
}
```

**Response:**
```json
{
  "question": "What is happening with NVDA today?",
  "symbol": "NVDA",
  "whatsHappeningNow": "NVDA is currently trading with elevated volume...",
  "keyDrivers": ["AI infrastructure demand", "Data center growth", "Competition dynamics"],
  "riskVsOpportunity": "The AI boom presents opportunity, but valuations are elevated...",
  "historicalBehavior": "Over 30-day periods, NVDA has been positive 68% of the time...",
  "simpleRecap": "NVDA is riding the AI wave with strong demand.",
  "generatedAt": "2024-01-15T10:30:00Z"
}
```

---

## Using Postman

1. **Import the collection** (optional): Import the Swagger spec from `http://localhost:8000/openapi.json`

2. **Set up requests**:
   - Base URL: `http://localhost:8000`
   - For POST requests, set `Content-Type: application/json` header

3. **Test endpoints**:
   - GET `{{base_url}}/health`
   - GET `{{base_url}}/ticker/AAPL/snapshot`
   - POST `{{base_url}}/outlook` with JSON body

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_ticker.py -v

# Run specific test
pytest tests/test_outlook_engine.py::TestVolatilityClassification -v
```

---

## Project Structure

```
daytrade-partner-data/
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies
├── .env                    # Environment variables (create this)
│
├── app/
│   ├── main.py             # FastAPI app factory
│   ├── api/                # HTTP routers
│   │   ├── health.py
│   │   ├── market.py       # /ticker endpoints
│   │   ├── outlook.py
│   │   └── ai.py           # /explain endpoint
│   ├── services/           # Business logic
│   │   ├── ticker_service.py
│   │   ├── outlook_engine.py
│   │   └── ai_service.py
│   ├── models/             # Pydantic schemas
│   └── core/               # Config, logging, errors
│
├── tests/                  # Test suite
└── docs/
    ├── PROJECT_GUIDE.md    # Architecture guide
    └── API_CONTRACT.md     # API specification
```

---

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_DATA` | `true` | Use mock data instead of live APIs |
| `OPENAI_API_KEY` | `""` | OpenAI API key for /explain |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `API_HOST` | `0.0.0.0` | Server host |
| `API_PORT` | `8000` | Server port |
| `DEBUG` | `false` | Enable debug mode |

---

## Architecture

```
┌────────────────────────────────────┐
│       TradeLens iOS App            │
│       (daytrade-partner)           │
└─────────────┬──────────────────────┘
              │ HTTP/JSON
              ▼
┌────────────────────────────────────┐
│     This Backend                   │
│     (daytrade-partner-data)        │
│                                    │
│  • Market data (yfinance)          │
│  • Statistical outlooks            │
│  • AI explanations (OpenAI)        │
└─────────────┬──────────────────────┘
              │
              ▼
        External APIs
        (Yahoo Finance, OpenAI)
```

### Key Principles

1. **iOS app talks ONLY to this backend** — No direct external API calls from the app
2. **Backend owns the data contracts** — Pydantic models define authoritative schemas
3. **Mock-first development** — All services work without external APIs
4. **No financial advice** — All outputs are descriptive, never predictive

---

## Documentation

- [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) — Architecture and development guide
- [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) — Endpoint specifications

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

Make sure you installed in editable mode:
```bash
pip install -e ".[dev]"
```

### Tests fail with network errors

Tests run with mock data by default. If you're seeing network errors:
```bash
USE_MOCK_DATA=true pytest tests/ -v
```

### OpenAI errors

Make sure your API key is set:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or set `USE_MOCK_DATA=true` to use fallback responses.

---

Built with FastAPI + Python 3.11
