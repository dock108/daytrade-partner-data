"""
Outlook endpoint for market outlook generation.

Computes descriptive statistics from historical price data.
All outputs are descriptive — no predictions or financial advice.
"""

from fastapi import APIRouter

from app.models.outlook import Outlook, OutlookRequest
from app.services.outlook_engine import OutlookEngine

router = APIRouter()
outlook_engine = OutlookEngine()


@router.post("/outlook", response_model=Outlook)
async def generate_outlook(request: OutlookRequest) -> Outlook:
    """
    Generate a structured outlook for a ticker.

    Computes rolling returns, hit rate, volatility metrics, and sentiment
    from historical price data. This provides descriptive metrics only —
    no predictions or financial advice.

    **Request Body:**
    - **symbol**: Stock/ETF ticker symbol (e.g., NVDA, AAPL)
    - **timeframeDays**: Outlook window in days (10-365, default 30)

    **Returns:**
    - Sentiment summary based on historical patterns
    - Key drivers affecting the ticker
    - Volatility band (typical range as percentage)
    - Historical hit rate (fraction of positive windows)
    """
    return await outlook_engine.compute_outlook(
        symbol=request.symbol,
        timeframe_days=request.timeframe_days,
    )
