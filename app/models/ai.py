"""
AI response models.

These models define the structured response format for AI-powered explanations.
"""

from pydantic import BaseModel, ConfigDict, Field


class AIResponse(BaseModel):
    """
    Structured AI response with 5 explanation fields.

    All fields are required. Content is descriptive — no predictions or financial advice.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "whatsHappeningNow": "NVIDIA shares are trading with elevated volume as investors digest AI infrastructure spending trends.",
                "keyDrivers": [
                    "AI infrastructure demand remains robust",
                    "Data center GPU orders accelerating",
                    "Competition dynamics evolving",
                ],
                "riskVsOpportunity": "The AI boom presents significant opportunity, but valuations are elevated. High volatility cuts both ways.",
                "historicalBehavior": "Over 30-day periods, NVDA has been positive 68% of the time, with typical swings of ±12%.",
                "simpleRecap": "NVDA is riding the AI wave with strong demand, but expect bigger price swings than average.",
            }
        },
    )

    whats_happening_now: str = Field(
        ...,
        alias="whatsHappeningNow",
        description="Current market situation summary",
    )
    key_drivers: list[str] = Field(
        ...,
        alias="keyDrivers",
        description="Key factors driving the current situation",
    )
    risk_vs_opportunity: str = Field(
        ...,
        alias="riskVsOpportunity",
        description="Balanced perspective on risks and opportunities",
    )
    historical_behavior: str = Field(
        ...,
        alias="historicalBehavior",
        description="Relevant historical context and patterns",
    )
    simple_recap: str = Field(
        ...,
        alias="simpleRecap",
        description="One-sentence summary in plain language",
    )


