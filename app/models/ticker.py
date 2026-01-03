"""
Ticker-related models.

These models align with the iOS app's TickerInfo.swift and PriceData.swift.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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
    def yfinance_period(self) -> str:
        """Convert to yfinance period string."""
        mapping = {
            ChartTimeRange.ONE_DAY: "1d",
            ChartTimeRange.ONE_MONTH: "1mo",
            ChartTimeRange.SIX_MONTHS: "6mo",
            ChartTimeRange.ONE_YEAR: "1y",
        }
        return mapping[self]

    @property
    def yfinance_interval(self) -> str:
        """Get appropriate interval for this range."""
        mapping = {
            ChartTimeRange.ONE_DAY: "5m",
            ChartTimeRange.ONE_MONTH: "1d",
            ChartTimeRange.SIX_MONTHS: "1d",
            ChartTimeRange.ONE_YEAR: "1d",
        }
        return mapping[self]

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
    """Snapshot information about a ticker. Aligns with iOS TickerInfo struct."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                "source": "yfinance",
            }
        }
    )

    ticker: str = Field(..., description="Stock/ETF ticker symbol")
    company_name: str = Field(..., description="Full company name")
    sector: str = Field(..., description="Market sector")
    market_cap: str = Field(..., description="Formatted market cap")
    volatility: VolatilityLevel = Field(..., description="Volatility classification")
    summary: str = Field(..., description="Brief company/ticker summary")
    current_price: float | None = Field(None, description="Current price", ge=0)
    change_percent: float | None = Field(None, description="Regular market change percent")
    week_52_high: float | None = Field(None, description="52-week high price", ge=0)
    week_52_low: float | None = Field(None, description="52-week low price", ge=0)
    timestamp: datetime = Field(..., description="When data was fetched")
    source: str = Field(..., description="Data source identifier")


class PricePoint(BaseModel):
    """A single price point for charting. Aligns with iOS PricePoint struct."""

    date: datetime = Field(..., description="Date/time of the price point")
    close: float = Field(..., description="Closing price", ge=0)
    high: float = Field(..., description="High price for the period", ge=0)
    low: float = Field(..., description="Low price for the period", ge=0)


class PriceHistory(BaseModel):
    """Price history for a ticker. Aligns with iOS PriceHistory struct."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "AAPL",
                "points": [
                    {"date": "2024-01-15T16:00:00Z", "close": 185.50, "high": 186.20, "low": 184.80}
                ],
                "current_price": 185.50,
                "change": 2.30,
                "change_percent": 1.26,
                "timestamp": "2024-01-15T16:00:00Z",
                "source": "yfinance",
            }
        }
    )

    ticker: str = Field(..., description="Stock/ETF ticker symbol")
    points: list[PricePoint] = Field(..., description="Historical price points")
    current_price: float = Field(..., description="Current/latest price", ge=0)
    change: float = Field(..., description="Absolute price change")
    change_percent: float = Field(..., description="Percentage price change")
    timestamp: datetime = Field(..., description="When data was fetched")
    source: str = Field(..., description="Data source identifier")

    @property
    def is_positive(self) -> bool:
        """Whether the change is positive."""
        return self.change >= 0

    @property
    def min_price(self) -> float:
        """Minimum low price in the history."""
        return min((p.low for p in self.points), default=0.0)

    @property
    def max_price(self) -> float:
        """Maximum high price in the history."""
        return max((p.high for p in self.points), default=0.0)
