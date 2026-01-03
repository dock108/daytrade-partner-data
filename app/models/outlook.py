"""
Outlook models.

These models align with the iOS app's OutlookEngine.swift Outlook struct.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OutlookRequest(BaseModel):
    """Request model for outlook generation."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "timeframeDays": 30,
            }
        },
    )

    symbol: str = Field(..., description="Stock/ETF ticker symbol")
    timeframe_days: Annotated[int, Field(ge=10, le=365, alias="timeframeDays")] = 30

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.upper().strip()


class SentimentSummary(str, Enum):
    """Sentiment categories — descriptive, not predictive."""

    POSITIVE = "positive"
    MIXED = "mixed"
    CAUTIOUS = "cautious"

    @property
    def description(self) -> str:
        """Detailed description of the sentiment."""
        descriptions = {
            SentimentSummary.POSITIVE: (
                "Recent trends and sector momentum look constructive, "
                "helping explain what traders may be reacting to."
            ),
            SentimentSummary.MIXED: (
                "Signals are mixed — supportive indicators sit alongside uncertainty."
            ),
            SentimentSummary.CAUTIOUS: (
                "Recent data points show more uncertainty or headwinds, "
                "which can make moves feel less clear."
            ),
        }
        return descriptions[self]

    @property
    def simple_description(self) -> str:
        """Simplified description for users preferring simple mode."""
        descriptions = {
            SentimentSummary.POSITIVE: (
                "Recent trends look constructive, which can make the picture feel clearer."
            ),
            SentimentSummary.MIXED: ("It's a mixed picture — some good signs, some uncertainty."),
            SentimentSummary.CAUTIOUS: ("There's more uncertainty than usual right now."),
        }
        return descriptions[self]


class Outlook(BaseModel):
    """
    Structured outlook for a ticker over a given timeframe.

    Aligns with iOS Outlook struct. Provides descriptive metrics only —
    no predictions or financial advice.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "NVDA",
                "timeframe_days": 30,
                "sentiment_summary": "positive",
                "key_drivers": [
                    "AI infrastructure spending trends",
                    "Semiconductor supply dynamics",
                    "Momentum indicators showing recent strength",
                ],
                "volatility_band": 0.12,
                "historical_hit_rate": 0.68,
                "personal_context": None,
                "volatility_warning": None,
                "timeframe_note": None,
                "generated_at": "2024-01-15T10:30:00Z",
                "source": "yfinance",
            }
        }
    )

    ticker: str = Field(..., description="Stock/ETF ticker symbol")
    timeframe_days: int = Field(..., description="Outlook window in days", ge=1)
    sentiment_summary: SentimentSummary = Field(..., description="Overall sentiment assessment")
    key_drivers: list[str] = Field(..., description="Key factors driving the outlook")
    volatility_band: float = Field(..., description="Typical swing as percentage", ge=0)
    historical_hit_rate: float = Field(
        ..., description="Fraction of similar windows with positive return", ge=0, le=1
    )
    personal_context: str | None = Field(None, description="Tailored note from user history")
    volatility_warning: str | None = Field(None, description="Warning if volatility is high")
    timeframe_note: str | None = Field(None, description="Note if timeframe differs from style")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this outlook was generated",
    )
    source: str = Field(default="yfinance", description="Data source identifier")


class OutlookComposerResponse(BaseModel):
    """Composed outlook response assembled from multiple services."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "big_picture": "Apple Inc. (AAPL) in Technology last traded at $190.15 "
                "(+0.42% today). Market cap 2.90T. Consumer electronics and software.",
                "what_could_move_it": [
                    {
                        "type": "earnings",
                        "ticker": "AAPL",
                        "date": "2024-03-12T13:00:00Z",
                        "confidence": "high",
                    }
                ],
                "expected_swings": {
                    "volatility_level": "moderate",
                    "typical_daily_range": 0.012,
                    "week_52_range": 0.42,
                    "last_change_percent": 0.0042,
                },
                "historical_behavior": {
                    "sample_size": 42,
                    "win_rate": 0.62,
                    "typical_range": 0.05,
                    "max_move": 0.18,
                    "notes": "Behavior clustered around earnings windows.",
                },
                "recent_articles": [
                    {
                        "headline": "Apple shares rise on services update",
                        "summary": "Investors reacted to margin commentary.",
                        "url": "https://example.com",
                        "published": "2024-01-15T08:00:00Z",
                        "relevance": 0.7,
                        "ticker_match": True,
                    }
                ],
            }
        }
    )

    big_picture: str = Field(..., description="High-level summary for the ticker")
    what_could_move_it: list[dict] = Field(
        ...,
        description="Upcoming catalysts that may impact price action",
    )
    expected_swings: dict[str, float | str] = Field(
        ...,
        description="Expected swing metrics derived from recent history",
    )
    historical_behavior: dict[str, float | int | str] = Field(
        ...,
        description="Descriptive historical behavior summary from the pattern engine",
    )
    recent_articles: list[dict] = Field(
        ...,
        description="Recent news articles relevant to the ticker",
    )


class OutlookComposerSources(BaseModel):
    """Data sources for each outlook component."""

    snapshot: str = Field(..., description="Source for snapshot data")
    history: str = Field(..., description="Source for price history data")
    catalysts: str = Field(..., description="Source for catalyst data")
    news: str = Field(..., description="Source for news data")
    patterns: str = Field(..., description="Source for pattern analysis")


class OutlookComposerTimestamps(BaseModel):
    """Timestamps for each component used in the outlook."""

    snapshot: datetime = Field(..., description="Snapshot timestamp")
    history: datetime = Field(..., description="History timestamp")
    catalysts: datetime = Field(..., description="Catalyst timestamp")
    news: datetime = Field(..., description="News timestamp")
    patterns: datetime = Field(..., description="Pattern timestamp")
    generated_at: datetime = Field(..., description="When the composed outlook was generated")


class OutlookComposerWithMeta(OutlookComposerResponse):
    """Composed outlook response with timestamps and data sources."""

    ticker: str = Field(..., description="Stock/ETF ticker symbol")
    timestamps: OutlookComposerTimestamps = Field(
        ...,
        description="Timestamps for the composed outlook inputs",
    )
    data_sources: OutlookComposerSources = Field(
        ...,
        description="Data sources for the composed outlook inputs",
    )
