# TradeLens API Contract

This document defines the HTTP endpoints and JSON schemas that the TradeLens iOS app relies on. The schemas here are authoritative — iOS models must align.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: TBD

## Authentication

Currently unauthenticated. Future versions will add API key or JWT authentication.

---

## Common Fields

Every API response includes:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | datetime | When the data was fetched (ISO 8601) |
| `source` | string | Data origin (`yfinance`, `openai`, `mock`) |

---

## Endpoints

### Health Check

Basic health check for service monitoring.

```
GET /health
```

**Response**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status ("healthy") |
| `timestamp` | datetime | Current server time (ISO 8601) |
| `version` | string | API version |

**Example Response**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0"
}
```

---

### Ticker Snapshot

Get company information and current price for a ticker.

```
GET /ticker/{symbol}/snapshot
```

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Stock/ETF ticker symbol (e.g., AAPL, NVDA) |

**Response Schema: TickerSnapshot**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `company_name` | string | Full company name |
| `sector` | string | Market sector |
| `market_cap` | string | Formatted market cap (e.g., "2.89T") |
| `volatility` | enum | Volatility level: `low`, `moderate`, `high` |
| `summary` | string | Brief company summary |
| `current_price` | number? | Current price |
| `change_percent` | number? | Price change percentage |
| `week_52_high` | number? | 52-week high price |
| `week_52_low` | number? | 52-week low price |
| `timestamp` | datetime | When data was fetched |
| `source` | string | Data source identifier |

**Example Response**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "market_cap": "2.89T",
  "volatility": "low",
  "summary": "Consumer electronics and software company.",
  "current_price": 185.50,
  "change_percent": 1.25,
  "week_52_high": 199.62,
  "week_52_low": 164.08,
  "timestamp": "2024-01-15T16:00:00Z",
  "source": "yfinance"
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 404 | Ticker not found |

---

### Ticker History

Get price history for charting.

```
GET /ticker/{symbol}/history
```

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Stock/ETF ticker symbol |

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `range` | enum | `1M` | Time range: `1D`, `1M`, `6M`, `1Y` |

**Response Schema: PriceHistory**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `points` | array[PricePoint] | Historical price points |
| `current_price` | number | Latest price |
| `change` | number | Absolute price change |
| `change_percent` | number | Percentage price change |
| `timestamp` | datetime | When data was fetched |
| `source` | string | Data source identifier |

**PricePoint Schema**

| Field | Type | Description |
|-------|------|-------------|
| `date` | datetime | Date/time of the price point (ISO 8601) |
| `close` | number | Closing price |
| `high` | number | High price for the period |
| `low` | number | Low price for the period |

**Example Response**

```json
{
  "ticker": "NVDA",
  "points": [
    {
      "date": "2024-01-02T16:00:00Z",
      "close": 480.25,
      "high": 482.50,
      "low": 478.00
    },
    {
      "date": "2024-01-03T16:00:00Z",
      "close": 485.10,
      "high": 487.20,
      "low": 481.30
    }
  ],
  "current_price": 485.10,
  "change": 4.85,
  "change_percent": 1.01,
  "timestamp": "2024-01-15T16:00:00Z",
  "source": "yfinance"
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 404 | Ticker not found |

---

### Outlook

Generate a statistical outlook for a ticker based on historical behavior.

```
GET /outlook
```

**Query Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ticker` | string | Yes | — | Stock/ETF ticker symbol |
| `timeframe_days` | integer | No | 30 | Outlook window (10-365 days) |

**Response Schema: Outlook**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `timeframe_days` | integer | Outlook window in days |
| `sentiment_summary` | enum | Sentiment: `positive`, `mixed`, `cautious` |
| `key_drivers` | array[string] | Key factors driving the outlook |
| `volatility_band` | number | Expected swing as percentage (0.08 = 8%) |
| `historical_hit_rate` | number | Fraction of similar windows with positive return (0-1) |
| `personal_context` | string? | Tailored note from user history |
| `volatility_warning` | string? | Warning if volatility is high |
| `timeframe_note` | string? | Note if timeframe differs from typical |
| `generated_at` | datetime | When outlook was generated (ISO 8601) |
| `source` | string | Data source identifier |

**Example Request**

```bash
curl "http://localhost:8000/outlook?ticker=NVDA&timeframe_days=30"
```

**Example Response**

```json
{
  "ticker": "NVDA",
  "timeframe_days": 30,
  "sentiment_summary": "positive",
  "key_drivers": [
    "AI infrastructure spending trends",
    "Semiconductor supply dynamics",
    "Momentum indicators showing recent strength"
  ],
  "volatility_band": 0.12,
  "historical_hit_rate": 0.68,
  "personal_context": null,
  "volatility_warning": null,
  "timeframe_note": null,
  "generated_at": "2024-01-15T10:30:00Z",
  "source": "yfinance"
}
```

**Sentiment Descriptions**

| Value | Description |
|-------|-------------|
| `positive` | Recent trends look constructive |
| `mixed` | Supportive indicators alongside uncertainty |
| `cautious` | More uncertainty or headwinds than usual |

---

### Explain

Generate an AI-powered explanation for a user query.

```
POST /explain
```

**Request Schema: ExplainRequest**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | User's question (1-500 chars) |
| `symbol` | string? | No | Optional ticker for context |

**Response Schema: AIResponse**

| Field | Type | Description |
|-------|------|-------------|
| `whats_happening_now` | string | Current market situation summary |
| `key_drivers` | array[string] | Key factors driving the situation |
| `risk_vs_opportunity` | string | Balanced risk/opportunity perspective |
| `historical_behavior` | string | Relevant historical context |
| `simple_recap` | string | One-sentence summary |

**Example Request**

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What'\''s happening with NVDA today?",
    "symbol": "NVDA"
  }'
```

**Example Response**

```json
{
  "whatsHappeningNow": "NVIDIA shares are trading with elevated volume as investors digest AI infrastructure spending trends.",
  "keyDrivers": [
    "AI infrastructure demand remains robust",
    "Data center GPU orders accelerating",
    "Competition dynamics evolving"
  ],
  "riskVsOpportunity": "The AI boom presents significant opportunity, but valuations are elevated.",
  "historicalBehavior": "Over 30-day periods, NVDA has been positive 68% of the time with typical swings of ±12%.",
  "simpleRecap": "NVDA is riding the AI wave with strong demand, but expect bigger price swings than average."
}
```

> **Note:** Response fields use `camelCase` for iOS compatibility. Use `populate_by_name=True` on the backend.

---

## iOS Model Alignment

This table shows how backend models align with iOS Swift structs:

| Backend Model | iOS Struct | Location |
|---------------|------------|----------|
| `TickerSnapshot` | `TickerInfo` | `TradeLens/Models/TickerInfo.swift` |
| `PriceHistory` | `PriceHistory` | `TradeLens/Models/PriceData.swift` |
| `PricePoint` | `PricePoint` | `TradeLens/Models/PriceData.swift` |
| `Outlook` | `Outlook` | `TradeLens/Models/Outlook.swift` |
| `AIResponse` | `AIResponse` | `TradeLens/Models/AIResponse.swift` |

## Field Naming Convention

Backend uses `snake_case`, iOS uses `camelCase`. The iOS app should use:

```swift
let decoder = JSONDecoder()
decoder.keyDecodingStrategy = .convertFromSnakeCase
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request — Invalid parameters |
| 404 | Not Found — Resource doesn't exist |
| 500 | Internal Server Error — Server-side failure |
| 502 | Bad Gateway — External service failure |

---

## Versioning

The API version is returned in the `/health` endpoint. Breaking changes will increment the major version, and the URL path will be updated (e.g., `/v2/ticker/...`).

Current version: **0.1.0**
