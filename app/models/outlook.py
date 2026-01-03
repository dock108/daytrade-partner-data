"""
Outlook models.

These models align with the iOS app's OutlookEngine.swift Outlook struct.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class OutlookRequest(BaseModel):
    """Request model for outlook generation."""

    symbol: str = Field(..., description="Stock/ETF ticker symbol", examples=["AAPL", "SPY"])
    timeframe_days: int = Field(
        default=30,
        ge=10,
        le=365,
        alias="timeframeDays",
        description="Outlook window in days (10-365)",
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.upper().strip()

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "timeframeDays": 30,
            }
        }


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
            SentimentSummary.MIXED: (
                "It's a mixed picture — some good signs, some uncertainty."
            ),
            SentimentSummary.CAUTIOUS: (
                "There's more uncertainty than usual right now."
            ),
        }
        return descriptions[self]


class Outlook(BaseModel):
    """
    Structured outlook for a ticker over a given timeframe.

    Aligns with iOS Outlook struct from OutlookEngine.swift.
    This provides descriptive metrics only — no predictions or financial advice.
    """

    ticker: str = Field(..., description="Stock/ETF ticker symbol")
    timeframe_days: int = Field(..., description="Outlook window in days", ge=1)
    sentiment_summary: SentimentSummary = Field(..., description="Overall sentiment assessment")
    key_drivers: list[str] = Field(..., description="Key factors driving the outlook")
    volatility_band: float = Field(
        ...,
        description="Expected swing as percentage (e.g., 0.08 = 8%)",
        ge=0,
    )
    historical_hit_rate: float = Field(
        ...,
        description="Percentage times ticker was up over similar windows",
        ge=0,
        le=1,
    )
    personal_context: str | None = Field(
        None,
        description="Tailored note from user's trade history",
    )
    volatility_warning: str | None = Field(
        None,
        description="Warning if volatility is above user's tolerance",
    )
    timeframe_note: str | None = Field(
        None,
        description="Note if timeframe differs from user's trading style",
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this outlook was generated",
    )

    class Config:
        json_schema_extra = {
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
                "personal_context": "Tech names have lined up with stronger results in your history.",
                "volatility_warning": None,
                "timeframe_note": None,
                "generated_at": "2024-01-15T10:30:00Z",
            }
        }

