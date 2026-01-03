"""
Market endpoints for ticker snapshot and price history data.

Uses yfinance for live market data with mock fallback.
"""

from fastapi import APIRouter, Query

from app.models.ticker import ChartTimeRange, PriceHistory, TickerSnapshot
from app.services.ticker_service import TickerService

router = APIRouter()
ticker_service = TickerService()


@router.get("/{symbol}/snapshot", response_model=TickerSnapshot)
async def get_ticker_snapshot(symbol: str) -> TickerSnapshot:
    """
    Get snapshot information for a ticker.

    Returns current market data including price, change, 52-week range,
    and company information.

    **Response fields:**
    - **ticker**: Symbol (uppercase)
    - **company_name**: Full company name
    - **sector**: Market sector
    - **market_cap**: Formatted market cap (e.g., "2.89T")
    - **volatility**: "low", "moderate", or "high"
    - **summary**: Brief company description
    - **current_price**: Current trading price
    - **change_percent**: Percentage change from previous close
    - **week_52_high**: 52-week high price
    - **week_52_low**: 52-week low price

    **Errors:**
    - 404: Unknown symbol
    - 502: External service unavailable
    """
    return await ticker_service.get_snapshot(symbol)


@router.get("/{symbol}/history", response_model=PriceHistory)
async def get_ticker_history(
    symbol: str,
    range: ChartTimeRange = Query(
        default=ChartTimeRange.ONE_MONTH,
        description="Time range: 1D, 1M, 6M, or 1Y",
    ),
) -> PriceHistory:
    """
    Get price history for a ticker.

    Returns historical price points for charting, plus change metrics.

    **Query params:**
    - **range**: Time range (1D, 1M, 6M, 1Y). Default: 1M

    **Response fields:**
    - **ticker**: Symbol (uppercase)
    - **points**: Array of {date, close, high, low}
    - **current_price**: Most recent closing price
    - **change**: Absolute price change over range
    - **change_percent**: Percentage change over range

    **Errors:**
    - 404: Unknown symbol
    - 502: External service unavailable
    """
    return await ticker_service.get_history(symbol, range)
