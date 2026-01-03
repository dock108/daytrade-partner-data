"""
Outlook endpoint for market outlook generation.
"""

from fastapi import APIRouter, Query

from app.models.outlook import Outlook
from app.services.outlook_service import OutlookService

router = APIRouter()
outlook_service = OutlookService()


@router.get("/outlook", response_model=Outlook)
async def get_outlook(
    ticker: str = Query(..., description="Stock/ETF ticker symbol"),
    timeframe_days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Outlook window in days",
    ),
) -> Outlook:
    """
    Generate a structured outlook for a ticker.

    Returns sentiment analysis, key drivers, volatility expectations,
    and historical context. This provides descriptive metrics only —
    no predictions or financial advice.

    - **ticker**: Stock/ETF ticker symbol (e.g., NVDA, AAPL)
    - **timeframe_days**: Outlook window in days (1-365, default 30)
    """
    return await outlook_service.generate_outlook(
        ticker=ticker,
        timeframe_days=timeframe_days,
    )

