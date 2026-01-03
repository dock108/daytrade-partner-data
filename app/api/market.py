"""
Market endpoints for ticker snapshot and price history data.
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

    Returns company info, sector, market cap, volatility level, and summary.

    - **symbol**: Stock/ETF ticker symbol (e.g., AAPL, NVDA)
    """
    return await ticker_service.get_snapshot(symbol)


@router.get("/{symbol}/history", response_model=PriceHistory)
async def get_ticker_history(
    symbol: str,
    range: ChartTimeRange = Query(
        default=ChartTimeRange.ONE_MONTH,
        description="Time range for historical data",
    ),
) -> PriceHistory:
    """
    Get price history for a ticker.

    Returns historical price points, current price, and change metrics.

    - **symbol**: Stock/ETF ticker symbol (e.g., AAPL, NVDA)
    - **range**: Time range (1D, 1M, 6M, 1Y)
    """
    return await ticker_service.get_history(symbol, range)
