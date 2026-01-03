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
