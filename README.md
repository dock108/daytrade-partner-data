# daytrade-partner-data

Backend API for the **TradeLens** iOS trading companion app.

Provides market data, statistical outlooks, and AI-powered explanations — all descriptive, never predictive.

## Quick Start

```bash
# Clone
git clone https://github.com/dock108/daytrade-partner-data.git
cd daytrade-partner-data

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure (optional - works without this)
echo "USE_MOCK_DATA=true" > .env
echo "OPENAI_API_KEY=sk-your-key" >> .env

# Run
uvicorn app.main:app --reload --port 8000
```

## Verify It Works

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ticker/{symbol}/snapshot` | GET | Company info, price, 52-week range |
| `/ticker/{symbol}/history` | GET | Price history for charting |
| `/outlook` | POST | Statistical outlook (hit rate, volatility) |
| `/explain` | POST | AI-powered market explanation |

**Interactive docs**: http://localhost:8000/docs

## Example Requests

```bash
# Ticker snapshot
curl http://localhost:8000/ticker/AAPL/snapshot

# Price history
curl "http://localhost:8000/ticker/NVDA/history?range=1M"

# Outlook
curl -X POST http://localhost:8000/outlook \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SPY", "timeframeDays": 30}'

# AI Explanation
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"question": "What is happening with AAPL?", "symbol": "AAPL"}'
```

## Running Tests

```bash
pytest tests/ -v
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) | Architecture and development guide |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Endpoint specifications |
| [docs/AGENTS.md](docs/AGENTS.md) | Context for AI coding assistants |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_DATA` | `true` | Use mock data (no external APIs needed) |
| `OPENAI_API_KEY` | `""` | OpenAI key for /explain endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |

---

Built with FastAPI + Python 3.11
