"""
AI explanation models.

These models align with the iOS app's AIResponse.swift for structured AI responses.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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

    query: str = Field(
        ...,
        description="User's question or topic to explain",
        min_length=1,
        max_length=500,
        examples=["What's happening with NVDA today?"],
    )
    ticker: str | None = Field(
        None,
        description="Optional ticker symbol for context",
        examples=["NVDA"],
    )
    include_sources: bool = Field(
        True,
        description="Whether to include source references",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's happening with NVDA today?",
                "ticker": "NVDA",
                "include_sources": True,
            }
        }


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
                        "content": "NVIDIA shares are trading higher today following positive analyst commentary on AI chip demand.",
                        "bullet_points": None,
                    },
                    {
                        "section_type": "key_drivers",
                        "content": "Several factors are driving the current movement.",
                        "bullet_points": [
                            "Strong data center GPU demand",
                            "New AI model training contracts",
                            "Supply chain improvements",
                        ],
                    },
                ],
                "sources": [
                    {
                        "title": "NVIDIA Sees Record AI Chip Orders",
                        "source": "Reuters",
                        "source_type": "news",
                        "summary": "Data center revenue up 40% YoY driven by enterprise AI adoption.",
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }

