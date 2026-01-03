"""
AI explanation request model.

The main response model (AIResponse) is in app/models/ai.py.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
