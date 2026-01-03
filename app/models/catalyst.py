"""
Catalyst calendar models.

These models define upcoming catalysts like earnings, dividends, splits, and
macro events for the TradeLens app.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CatalystType(str, Enum):
    """Supported catalyst types."""

    EARNINGS = "earnings"
    DIVIDEND = "dividend"
    SPLIT = "split"
    FED_MEETING = "fed"
    CPI = "cpi"
    PPI = "ppi"
    SECTOR = "sector"


class ConfidenceLevel(str, Enum):
    """Confidence level for each catalyst."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CatalystEvent(BaseModel):
    """Single catalyst calendar event."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "earnings",
                "ticker": "UNH",
                "date": "2024-03-12T13:00:00Z",
                "confidence": "high",
            }
        }
    )

    type: CatalystType = Field(..., description="Catalyst event type")
    ticker: str | None = Field(
        None,
        description="Ticker symbol or sector ETF for sector events",
    )
    date: datetime = Field(..., description="Scheduled event time in UTC")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        """Normalize ticker symbols to uppercase."""
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None
