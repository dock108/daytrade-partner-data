"""
AI explanation models.

These models align with the iOS app's AIResponse.swift for structured AI responses.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SectionType(str, Enum):
    """Types of sections in an AI response."""

    CURRENT_SITUATION = "current_situation"
    KEY_DRIVERS = "key_drivers"
    RISK_OPPORTUNITY = "risk_opportunity"
    HISTORICAL = "historical"
    RECAP = "recap"
    YOUR_CONTEXT = "your_context"
    PERSONAL_NOTE = "personal_note"
    DIGEST = "digest"

    @property
    def display_name(self) -> str:
        """Human-readable section title."""
        names = {
            SectionType.CURRENT_SITUATION: "What's happening now",
            SectionType.KEY_DRIVERS: "Key drivers",
            SectionType.RISK_OPPORTUNITY: "Risk vs opportunity",
            SectionType.HISTORICAL: "Historical context",
            SectionType.RECAP: "Quick take",
            SectionType.YOUR_CONTEXT: "Your trading context",
            SectionType.PERSONAL_NOTE: "Personal note",
            SectionType.DIGEST: "Here's the story in simple terms",
        }
        return names[self]


class SourceType(str, Enum):
    """Types of source references."""

    NEWS = "news"
    RESEARCH = "research"
    FILINGS = "filings"
    ANALYSIS = "analysis"


class SourceReference(BaseModel):
    """A source reference for deeper reading."""

    title: str = Field(..., description="Source title")
    source: str = Field(..., description="Source name/publication")
    source_type: SourceType = Field(..., description="Type of source")
    summary: str = Field(..., description="Brief summary of the source content")


class ResponseSection(BaseModel):
    """A section of the AI response."""

    section_type: SectionType = Field(..., description="Type of section")
    content: str = Field(..., description="Main content of the section")
    bullet_points: list[str] | None = Field(None, description="Optional bullet points")


class ExplainRequest(BaseModel):
    """Request body for the /explain endpoint."""

    question: str = Field(
        ...,
        description="User's question about the market or ticker",
        min_length=1,
        max_length=500,
        examples=["What's happening with NVDA today?"],
    )
    symbol: str | None = Field(
        None,
        description="Optional ticker symbol for context",
        examples=["NVDA"],
    )
    timeframe_days: int | None = Field(
        None,
        ge=10,
        le=365,
        alias="timeframeDays",
        description="Timeframe for historical analysis (10-365 days)",
    )
    simple_mode: bool = Field(
        False,
        alias="simpleMode",
        description="Use simpler language without jargon",
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str | None) -> str | None:
        """Normalize symbol to uppercase."""
        return v.upper().strip() if v else None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "question": "What's happening with NVDA today?",
                "symbol": "NVDA",
                "timeframeDays": 30,
                "simpleMode": False,
            }
        }


class AIResponse(BaseModel):
    """
    Structured AI response with 5 explanation fields.

    Aligns with iOS AIResponse struct. All content is descriptive —
    no predictions or financial advice.
    """

    question: str = Field(..., description="The original question")
    symbol: str | None = Field(None, description="Ticker symbol if provided")
    whats_happening_now: str = Field(
        ...,
        alias="whatsHappeningNow",
        description="Current situation description",
    )
    key_drivers: list[str] = Field(
        ...,
        alias="keyDrivers",
        description="Key factors driving the situation",
    )
    risk_vs_opportunity: str = Field(
        ...,
        alias="riskVsOpportunity",
        description="Balanced perspective on risks and opportunities",
    )
    historical_behavior: str = Field(
        ...,
        alias="historicalBehavior",
        description="Historical context and patterns",
    )
    simple_recap: str = Field(
        ...,
        alias="simpleRecap",
        description="Single sentence summary in plain language",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="When this response was generated",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "question": "What's happening with NVDA today?",
                "symbol": "NVDA",
                "whatsHappeningNow": "NVIDIA shares are trading with elevated volume today as investors digest recent AI infrastructure spending trends.",
                "keyDrivers": [
                    "AI infrastructure demand remains robust",
                    "Data center GPU orders accelerating",
                    "Competition dynamics evolving",
                    "Supply chain improvements",
                ],
                "riskVsOpportunity": "The AI boom presents significant opportunity, but valuations are elevated. The stock has shown high volatility, which cuts both ways.",
                "historicalBehavior": "Over 30-day periods, NVDA has been positive 68% of the time, with typical swings of ±12%. High volatility is normal for this name.",
                "simpleRecap": "NVDA is riding the AI wave with strong demand, but expect bigger price swings than average.",
                "generatedAt": "2024-01-15T10:30:00Z",
            }
        }


# Legacy models for backwards compatibility
class ExplainResponse(BaseModel):
    """
    Structured AI response broken into readable sections.

    Aligns with iOS AIResponse struct.
    """

    query: str = Field(..., description="The original query")
    sections: list[ResponseSection] = Field(..., description="Response sections")
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Source references for deeper reading",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's happening with NVDA today?",
                "sections": [
                    {
                        "section_type": "current_situation",
                        "content": "NVIDIA shares are trading higher today.",
                        "bullet_points": None,
                    },
                ],
                "sources": [],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
