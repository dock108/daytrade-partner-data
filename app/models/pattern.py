"""
Behavior pattern models.

Descriptive statistics for historical periods sharing similar context.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BehaviorPatternRequest(BaseModel):
    """Request model for behavior pattern analysis."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "context": ["earnings", "high inflation", "fed week"],
            }
        },
    )

    symbol: str = Field(..., description="Stock/ETF ticker symbol")
    context: list[str] = Field(
        default_factory=list,
        description="Context tags like earnings period, inflation, or Fed week",
        max_length=12,
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.upper().strip()

    @field_validator("context")
    @classmethod
    def normalize_context(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value if item.strip()]


class BehaviorPattern(BaseModel):
    """Behavior pattern summary for similar historical conditions."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sample_size": 42,
                "win_rate": 0.62,
                "typical_range": 0.05,
                "max_move": 0.18,
                "notes": "Behavior clustered around earnings cycles.",
            }
        }
    )

    sample_size: int = Field(..., description="Number of similar historical samples", ge=0)
    win_rate: float = Field(
        ..., description="Fraction of samples with positive return", ge=0, le=1
    )
    typical_range: float = Field(
        ..., description="Median swing range as percentage", ge=0
    )
    max_move: float = Field(
        ..., description="Largest absolute move observed", ge=0
    )
    notes: str = Field(
        ..., description="Descriptive context notes without forward-looking claims"
    )
