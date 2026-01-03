"""
Behavior pattern endpoint.

Provides descriptive statistics for historical periods sharing similar context.
All outputs are descriptive — no predictions or financial advice.
"""

from fastapi import APIRouter

from app.models.pattern import BehaviorPattern, BehaviorPatternRequest
from app.services.pattern_engine import PatternEngine

router = APIRouter()
pattern_engine = PatternEngine()


@router.post("/pattern", response_model=BehaviorPattern)
async def generate_pattern(request: BehaviorPatternRequest) -> BehaviorPattern:
    """
    Generate historical behavior pattern metrics for a ticker + context.

    **Request Body:**
    - **symbol**: Stock/ETF ticker symbol (e.g., NVDA, AAPL)
    - **context**: Context tags like earnings period, high inflation, Fed week

    **Returns:**
    - Sample size of similar historical windows
    - Win rate (% of periods with positive return)
    - Typical swing range
    - Max move outlier
    - Descriptive notes (no prediction language)
    """
    return await pattern_engine.compute_pattern(
        symbol=request.symbol,
        context=request.context,
    )
