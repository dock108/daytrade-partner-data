"""
Explain endpoint for AI-powered explanations.
"""

from fastapi import APIRouter

from app.models.explain import ExplainRequest, ExplainResponse
from app.services.explain_service import ExplainService

router = APIRouter()
explain_service = ExplainService()


@router.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest) -> ExplainResponse:
    """
    Generate a structured AI explanation for a user query.

    Returns an article-style response broken into sections with optional sources.
    Think of this as "Google for stocks" — it provides context and understanding,
    not predictions or financial advice.

    - **query**: User's question or topic to explain
    - **ticker**: Optional ticker symbol for context
    - **include_sources**: Whether to include source references (default true)
    """
    return await explain_service.explain(request)

