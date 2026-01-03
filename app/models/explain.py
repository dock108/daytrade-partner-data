"""
AI explanation models.

These models align with the iOS app's AIResponse.swift for structured AI responses.
"""

from datetime import datetime
from enum import Enum

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "What's happening with NVDA today?",
                "symbol": "NVDA",
                "timeframeDays": 30,
                "simpleMode": False,
            }
        },
    )

    question: str = Field(..., description="User's question", min_length=1, max_length=500)
    symbol: str | None = Field(None, description="Optional ticker symbol for context")
    timeframe_days: Annotated[int | None, Field(ge=10, le=365, alias="timeframeDays")] = None
    simple_mode: Annotated[bool, Field(alias="simpleMode")] = False

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str | None) -> str | None:
        """Normalize symbol to uppercase."""
        return v.upper().strip() if v else None


class AIResponse(BaseModel):
    """
    Structured AI response with 5 explanation fields.

    Aligns with iOS AIResponse struct. All content is descriptive —
    no predictions or financial advice.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "What's happening with NVDA today?",
                "symbol": "NVDA",
                "whatsHappeningNow": "NVIDIA shares are trading with elevated volume...",
                "keyDrivers": ["AI infrastructure demand", "Data center growth"],
                "riskVsOpportunity": "The AI boom presents opportunity, but valuations are elevated.",
                "historicalBehavior": "Over 30-day periods, NVDA has been positive 68% of the time.",
                "simpleRecap": "NVDA is riding the AI wave with strong demand.",
                "generatedAt": "2024-01-15T10:30:00Z",
            }
        },
    )

    question: str = Field(..., description="The original question")
    symbol: str | None = Field(None, description="Ticker symbol if provided")
    whats_happening_now: str = Field(
        ..., alias="whatsHappeningNow", description="Current situation"
    )
    key_drivers: list[str] = Field(..., alias="keyDrivers", description="Key factors")
    risk_vs_opportunity: str = Field(..., alias="riskVsOpportunity", description="Risk/opportunity")
    historical_behavior: str = Field(
        ..., alias="historicalBehavior", description="Historical context"
    )
    simple_recap: str = Field(..., alias="simpleRecap", description="One-sentence summary")
    generated_at: datetime = Field(..., alias="generatedAt", description="Generation timestamp")


# Legacy model for backwards compatibility (not actively used)
class ExplainResponse(BaseModel):
    """Legacy response model with sections. Kept for backwards compatibility."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What's happening with NVDA today?",
                "sections": [],
                "sources": [],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
    )

    query: str = Field(..., description="The original query")
    sections: list[ResponseSection] = Field(..., description="Response sections")
    sources: list[SourceReference] = Field(default_factory=list, description="Source references")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
