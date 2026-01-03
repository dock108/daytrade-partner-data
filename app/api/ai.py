"""
AI endpoint for AI-powered market explanations.

All responses are descriptive — no predictions or financial advice.
"""

from fastapi import APIRouter

from app.models.explain import AIResponse, ExplainRequest
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()


@router.post("/explain", response_model=AIResponse)
async def explain(request: ExplainRequest) -> AIResponse:
    """
    Generate a structured AI explanation for a market question.

    Returns a response with 5 explanation fields covering the current situation,
    key drivers, risk/opportunity balance, historical behavior, and a simple recap.

    This provides educational context and understanding — no predictions or
    financial advice.

    **Request Body:**
    - **question**: User's question about the market or a ticker
    - **symbol**: Optional ticker symbol for context (e.g., NVDA, AAPL)
    - **timeframeDays**: Optional timeframe for historical analysis (10-365, default 30)
    - **simpleMode**: Use simpler language without jargon (default false)

    **Returns:**
    - **whatsHappeningNow**: Current situation description
    - **keyDrivers**: Array of key factors
    - **riskVsOpportunity**: Balanced perspective
    - **historicalBehavior**: Historical context
    - **simpleRecap**: Single sentence summary
    """
    return await ai_service.generate_explanation(
        question=request.question,
        symbol=request.symbol,
        timeframe_days=request.timeframe_days,
        simple_mode=request.simple_mode,
    )
