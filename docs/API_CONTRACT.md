# TradeLens API Contract

This document defines the HTTP endpoints and JSON schemas that the TradeLens iOS app relies on. Even when endpoints are initially mocked, the contract here is authoritative.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: TBD

## Authentication

Currently unauthenticated. Future versions will add API key or JWT authentication.

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

Get company information and metadata for a ticker.

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

**Example Request**

```bash
curl http://localhost:8000/ticker/AAPL/snapshot
```

**Example Response**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "market_cap": "2.89T",
  "volatility": "low",
  "summary": "Consumer electronics and software company known for iPhone, Mac, and services ecosystem."
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

**PricePoint Schema**

| Field | Type | Description |
|-------|------|-------------|
| `date` | datetime | Date/time of the price point (ISO 8601) |
| `close` | number | Closing price |
| `high` | number | High price for the period |
| `low` | number | Low price for the period |

**Example Request**

```bash
curl "http://localhost:8000/ticker/NVDA/history?range=1M"
```

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
  "change_percent": 1.01
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 404 | Ticker not found |

---

### Outlook

Generate a structured market outlook for a ticker.

```
GET /outlook
```

**Query Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ticker` | string | Yes | — | Stock/ETF ticker symbol |
| `timeframe_days` | integer | No | 30 | Outlook window (1-365 days) |

**Response Schema: Outlook**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `timeframe_days` | integer | Outlook window in days |
| `sentiment_summary` | enum | Sentiment: `positive`, `mixed`, `cautious` |
| `key_drivers` | array[string] | Key factors driving the outlook |
| `volatility_band` | number | Expected swing as percentage (0.08 = 8%) |
| `historical_hit_rate` | number | Percentage times ticker was up (0-1) |
| `personal_context` | string? | Tailored note from user history |
| `volatility_warning` | string? | Warning if above user tolerance |
| `timeframe_note` | string? | Note if timeframe differs from style |
| `generated_at` | datetime | When outlook was generated (ISO 8601) |

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
    "Cloud computing growth rates",
    "Momentum indicators showing recent strength"
  ],
  "volatility_band": 0.12,
  "historical_hit_rate": 0.68,
  "personal_context": null,
  "volatility_warning": null,
  "timeframe_note": null,
  "generated_at": "2024-01-15T10:30:00Z"
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
| `query` | string | Yes | User's question (1-500 chars) |
| `ticker` | string? | No | Optional ticker for context |
| `include_sources` | boolean | No | Include sources (default: true) |

**Response Schema: ExplainResponse**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original query |
| `sections` | array[ResponseSection] | Response sections |
| `sources` | array[SourceReference] | Source references |
| `timestamp` | datetime | When generated (ISO 8601) |

**ResponseSection Schema**

| Field | Type | Description |
|-------|------|-------------|
| `section_type` | enum | Section type (see below) |
| `content` | string | Main section content |
| `bullet_points` | array[string]? | Optional bullet points |

**Section Types**

| Value | Display Name |
|-------|--------------|
| `current_situation` | What's happening now |
| `key_drivers` | Key drivers |
| `risk_opportunity` | Risk vs opportunity |
| `historical` | Historical context |
| `recap` | Quick take |
| `your_context` | Your trading context |
| `personal_note` | Personal note |
| `digest` | Here's the story in simple terms |

**SourceReference Schema**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Source title |
| `source` | string | Source name/publication |
| `source_type` | enum | Type: `news`, `research`, `filings`, `analysis` |
| `summary` | string | Brief summary |

**Example Request**

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What'\''s happening with NVDA today?",
    "ticker": "NVDA",
    "include_sources": true
  }'
```

**Example Response**

```json
{
  "query": "What's happening with NVDA today?",
  "sections": [
    {
      "section_type": "current_situation",
      "content": "NVIDIA shares are trading higher today following positive analyst commentary on AI chip demand.",
      "bullet_points": null
    },
    {
      "section_type": "key_drivers",
      "content": "Several factors are driving the current movement.",
      "bullet_points": [
        "AI infrastructure demand remains robust",
        "Data center GPU orders accelerating",
        "Supply chain constraints easing"
      ]
    },
    {
      "section_type": "risk_opportunity",
      "content": "For NVDA, the risk/reward setup depends on your timeframe. Near-term volatility could present opportunities.",
      "bullet_points": null
    },
    {
      "section_type": "recap",
      "content": "In short: NVDA is navigating a dynamic environment with multiple catalysts in play.",
      "bullet_points": null
    }
  ],
  "sources": [
    {
      "title": "NVIDIA Sees Record AI Chip Orders",
      "source": "Reuters",
      "source_type": "news",
      "summary": "Data center revenue up 40% YoY driven by enterprise AI adoption."
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## iOS Model Alignment

This table shows how backend models align with iOS Swift structs:

| Backend Model | iOS Struct | Location |
|---------------|------------|----------|
| `TickerSnapshot` | `TickerInfo` | `TradeLens/Models/TickerInfo.swift` |
| `PriceHistory` | `PriceHistory` | `TradeLens/Models/PriceData.swift` |
| `PricePoint` | `PricePoint` | `TradeLens/Models/PriceData.swift` |
| `Outlook` | `Outlook` | `TradeLens/Services/OutlookEngine.swift` |
| `ExplainResponse` | `AIResponse` | `TradeLens/Models/AIResponse.swift` |
| `ResponseSection` | `AIResponse.Section` | `TradeLens/Models/AIResponse.swift` |
| `SourceReference` | `AIResponse.SourceReference` | `TradeLens/Models/AIResponse.swift` |

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

