"""
Ticker-related models.

These models align with the iOS app's TickerInfo.swift and PriceData.swift.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VolatilityLevel(str, Enum):
    """Volatility classification for a ticker."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ChartTimeRange(str, Enum):
    """Time range options for price history."""

    ONE_DAY = "1D"
    ONE_MONTH = "1M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"

    @property
    def days(self) -> int:
        """Number of days for each range."""
        mapping = {
            ChartTimeRange.ONE_DAY: 1,
            ChartTimeRange.ONE_MONTH: 30,
            ChartTimeRange.SIX_MONTHS: 180,
            ChartTimeRange.ONE_YEAR: 365,
        }
        return mapping[self]


class TickerSnapshot(BaseModel):
    """
    Snapshot information about a ticker.

    Aligns with iOS TickerInfo struct.
    """

    ticker: str = Field(..., description="Stock/ETF ticker symbol", examples=["AAPL"])
    company_name: str = Field(..., description="Full company name", examples=["Apple Inc."])
    sector: str = Field(..., description="Market sector", examples=["Technology"])
    market_cap: str = Field(..., description="Formatted market cap", examples=["2.89T"])
    volatility: VolatilityLevel = Field(..., description="Volatility classification")
    summary: str = Field(
        ...,
        description="Brief company/ticker summary",
        examples=["Consumer electronics and software company known for iPhone, Mac, and services."],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "market_cap": "2.89T",
                "volatility": "low",
                "summary": "Consumer electronics and software company known for iPhone, Mac, and services ecosystem.",
            }
        }


class PricePoint(BaseModel):
    """
    A single price point for charting.

    Aligns with iOS PricePoint struct.
    """

    date: datetime = Field(..., description="Date/time of the price point")
    close: float = Field(..., description="Closing price", ge=0)
    high: float = Field(..., description="High price for the period", ge=0)
    low: float = Field(..., description="Low price for the period", ge=0)


class PriceHistory(BaseModel):
    """
    Price history for a ticker.

    Aligns with iOS PriceHistory struct.
    """

    ticker: str = Field(..., description="Stock/ETF ticker symbol")
    points: list[PricePoint] = Field(..., description="Historical price points")
    current_price: float = Field(..., description="Current/latest price", ge=0)
    change: float = Field(..., description="Absolute price change")
    change_percent: float = Field(..., description="Percentage price change")

    @property
    def is_positive(self) -> bool:
        """Whether the change is positive."""
        return self.change >= 0

    @property
    def min_price(self) -> float:
        """Minimum low price in the history."""
        if not self.points:
            return 0.0
        return min(p.low for p in self.points)

    @property
    def max_price(self) -> float:
        """Maximum high price in the history."""
        if not self.points:
            return 0.0
        return max(p.high for p in self.points)

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "points": [
                    {"date": "2024-01-15T16:00:00Z", "close": 185.50, "high": 186.20, "low": 184.80}
                ],
                "current_price": 185.50,
                "change": 2.30,
                "change_percent": 1.26,
            }
        }

