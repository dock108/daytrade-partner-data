"""
AI explanation service.

Generates structured explanations for user queries,
initially with mock responses and later integrated with OpenAI.
"""

from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.models.explain import (
    ExplainRequest,
    ExplainResponse,
    ResponseSection,
    SectionType,
    SourceReference,
    SourceType,
)

logger = get_logger(__name__)


class ExplainService:
    """Service for generating AI-powered explanations."""

    async def explain(self, request: ExplainRequest) -> ExplainResponse:
        """
        Generate a structured explanation for a user query.

        Args:
            request: The explain request with query and options.

        Returns:
            Structured ExplainResponse with sections and sources.
        """
        logger.info(f"Generating explanation for: {request.query[:50]}...")

        if settings.USE_MOCK_DATA or not settings.OPENAI_API_KEY:
            return self._generate_mock_response(request)

        # TODO: Implement OpenAI integration
        return self._generate_mock_response(request)

    def _generate_mock_response(self, request: ExplainRequest) -> ExplainResponse:
        """Generate a mock AI response."""
        ticker = request.ticker or self._extract_ticker(request.query)

        sections: list[ResponseSection] = []

        # Current situation section
        sections.append(
            ResponseSection(
                section_type=SectionType.CURRENT_SITUATION,
                content=self._generate_situation_content(request.query, ticker),
                bullet_points=None,
            )
        )

        # Key drivers section
        sections.append(
            ResponseSection(
                section_type=SectionType.KEY_DRIVERS,
                content="Several factors are driving the current market dynamics.",
                bullet_points=self._generate_driver_bullets(ticker),
            )
        )

        # Risk vs opportunity section
        sections.append(
            ResponseSection(
                section_type=SectionType.RISK_OPPORTUNITY,
                content=self._generate_risk_content(ticker),
                bullet_points=None,
            )
        )

        # Quick recap section
        sections.append(
            ResponseSection(
                section_type=SectionType.RECAP,
                content=self._generate_recap(ticker),
                bullet_points=None,
            )
        )

        # Add sources if requested
        sources: list[SourceReference] = []
        if request.include_sources:
            sources = self._generate_mock_sources(ticker)

        return ExplainResponse(
            query=request.query,
            sections=sections,
            sources=sources,
            timestamp=datetime.utcnow(),
        )

    def _extract_ticker(self, query: str) -> str | None:
        """Try to extract a ticker symbol from the query."""
        # Simple extraction: look for uppercase words that might be tickers
        words = query.upper().split()
        known_tickers = {"NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "SPY", "QQQ", "AMD"}

        for word in words:
            clean_word = "".join(c for c in word if c.isalpha())
            if clean_word in known_tickers:
                return clean_word

        return None

    def _generate_situation_content(self, query: str, ticker: str | None) -> str:
        """Generate the current situation content."""
        if ticker:
            return (
                f"{ticker} is showing interesting market dynamics today. "
                f"Trading volume has been above average, and price action suggests "
                f"institutional participation in the recent moves."
            )
        return (
            "The broader market is navigating several cross-currents right now. "
            "Economic data continues to influence Fed expectations, "
            "while earnings season provides company-specific catalysts."
        )

    def _generate_driver_bullets(self, ticker: str | None) -> list[str]:
        """Generate key driver bullet points."""
        if ticker in {"NVDA", "AMD"}:
            return [
                "AI infrastructure demand remains robust",
                "Data center GPU orders accelerating",
                "Supply chain constraints easing",
                "Competition dynamics evolving",
            ]
        elif ticker in {"AAPL", "MSFT", "GOOGL"}:
            return [
                "Enterprise software spending trends",
                "Consumer device refresh cycles",
                "Cloud computing growth rates",
                "AI integration roadmap",
            ]
        else:
            return [
                "Macroeconomic conditions and Fed policy",
                "Sector rotation patterns",
                "Earnings expectations vs. reality",
                "Technical support and resistance levels",
            ]

    def _generate_risk_content(self, ticker: str | None) -> str:
        """Generate risk vs opportunity content."""
        if ticker:
            return (
                f"For {ticker}, the risk/reward setup depends on your timeframe. "
                f"Near-term volatility could present opportunities for active traders, "
                f"while longer-term investors may focus on fundamental trends."
            )
        return (
            "The current market environment presents both opportunities and risks. "
            "Diversification and position sizing remain important considerations."
        )

    def _generate_recap(self, ticker: str | None) -> str:
        """Generate the quick recap."""
        if ticker:
            return (
                f"In short: {ticker} is navigating a dynamic environment with "
                f"multiple catalysts in play. Stay focused on your strategy."
            )
        return "The market is doing what markets do — presenting both challenges and opportunities."

    def _generate_mock_sources(self, ticker: str | None) -> list[SourceReference]:
        """Generate mock source references."""
        sources = []

        if ticker:
            sources.append(
                SourceReference(
                    title=f"{ticker} Sees Strong Institutional Interest",
                    source="Reuters",
                    source_type=SourceType.NEWS,
                    summary="Recent 13F filings show increased hedge fund positioning.",
                )
            )
            sources.append(
                SourceReference(
                    title=f"Technical Analysis: {ticker} Chart Patterns",
                    source="TradingView",
                    source_type=SourceType.ANALYSIS,
                    summary="Key support and resistance levels to watch.",
                )
            )
        else:
            sources.append(
                SourceReference(
                    title="Fed Minutes Reveal Policy Deliberations",
                    source="Federal Reserve",
                    source_type=SourceType.FILINGS,
                    summary="Committee members discussed data-dependent approach.",
                )
            )

        return sources

