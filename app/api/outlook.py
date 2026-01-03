"""
Outlook endpoint for market outlook generation.

Computes descriptive statistics from historical price data.
All outputs are descriptive — no predictions or financial advice.
"""

from fastapi import APIRouter

from app.models.outlook import Outlook, OutlookComposerWithMeta, OutlookRequest
from app.services.outlook_engine import OutlookComposer, OutlookEngine

router = APIRouter()
outlook_engine = OutlookEngine()
outlook_composer = OutlookComposer()


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


@router.get("/outlook/{ticker}", response_model=OutlookComposerWithMeta)
async def get_outlook_summary(ticker: str) -> OutlookComposerWithMeta:
    """
    Return a composed outlook summary for a ticker.

    Includes structured sections (big picture, catalysts, expected swings,
    historical behavior, and recent articles), plus timestamps and data sources
    for each component.
    """
    return await outlook_composer.compose_outlook_with_meta(ticker)
