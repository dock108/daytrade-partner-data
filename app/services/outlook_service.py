"""
Outlook generation service.

Synthesizes market data into structured outlooks — descriptive metrics only,
no predictions or financial advice.
"""

import random
from datetime import datetime

from app.core.logging import get_logger
from app.models.outlook import Outlook, SentimentSummary

logger = get_logger(__name__)


class OutlookService:
    """Service for generating structured market outlooks."""

    # Sector trends (mock data)
    _SECTOR_TRENDS: dict[str, tuple[SentimentSummary, float]] = {
        "Technology": (SentimentSummary.POSITIVE, 0.72),
        "Healthcare": (SentimentSummary.MIXED, 0.48),
        "Energy": (SentimentSummary.CAUTIOUS, 0.35),
        "Financials": (SentimentSummary.POSITIVE, 0.61),
        "Consumer Discretionary": (SentimentSummary.MIXED, 0.52),
        "Consumer Staples": (SentimentSummary.POSITIVE, 0.58),
        "Industrials": (SentimentSummary.MIXED, 0.49),
        "Materials": (SentimentSummary.CAUTIOUS, 0.41),
        "Utilities": (SentimentSummary.POSITIVE, 0.55),
        "Real Estate": (SentimentSummary.CAUTIOUS, 0.38),
        "Communication Services": (SentimentSummary.MIXED, 0.53),
        "Broad Market": (SentimentSummary.MIXED, 0.55),
    }

    # Ticker metadata (mock)
    _TICKER_METADATA: dict[str, dict] = {
        "NVDA": {"sector": "Technology", "base_volatility": 0.12, "historical_up_rate": 0.68},
        "AAPL": {"sector": "Technology", "base_volatility": 0.06, "historical_up_rate": 0.62},
        "MSFT": {"sector": "Technology", "base_volatility": 0.05, "historical_up_rate": 0.64},
        "GOOGL": {"sector": "Communication Services", "base_volatility": 0.07, "historical_up_rate": 0.58},
        "AMZN": {"sector": "Consumer Discretionary", "base_volatility": 0.08, "historical_up_rate": 0.60},
        "META": {"sector": "Communication Services", "base_volatility": 0.10, "historical_up_rate": 0.55},
        "TSLA": {"sector": "Consumer Discretionary", "base_volatility": 0.18, "historical_up_rate": 0.52},
        "SPY": {"sector": "Broad Market", "base_volatility": 0.04, "historical_up_rate": 0.65},
        "QQQ": {"sector": "Technology", "base_volatility": 0.06, "historical_up_rate": 0.63},
        "AMD": {"sector": "Technology", "base_volatility": 0.14, "historical_up_rate": 0.56},
    }

    # Key drivers by sector
    _SECTOR_DRIVERS: dict[str, list[str]] = {
        "Technology": [
            "AI infrastructure spending trends",
            "Enterprise software demand",
            "Semiconductor supply dynamics",
            "Consumer tech refresh cycles",
            "Cloud computing growth rates",
        ],
        "Healthcare": [
            "Drug pipeline developments",
            "Medicare/Medicaid policy changes",
            "Biotech funding environment",
            "Hospital admission trends",
            "Insurance coverage dynamics",
        ],
        "Energy": [
            "OPEC+ production decisions",
            "U.S. shale output levels",
            "Global demand signals",
            "Geopolitical risk premium",
            "Energy transition policies",
        ],
        "Financials": [
            "Interest rate trajectory",
            "Credit quality trends",
            "M&A activity levels",
            "Regulatory environment",
            "Consumer lending demand",
        ],
        "Consumer Discretionary": [
            "Consumer confidence levels",
            "Employment trends",
            "Wage growth dynamics",
            "E-commerce penetration",
            "Discretionary spending patterns",
        ],
        "Broad Market": [
            "Federal Reserve policy stance",
            "Corporate earnings trajectory",
            "Economic growth indicators",
            "Inflation trends",
            "Market breadth signals",
        ],
        "Communication Services": [
            "Digital advertising spend",
            "Streaming subscriber trends",
            "Social media engagement",
            "Content investment cycles",
            "Regulatory scrutiny levels",
        ],
    }

    async def generate_outlook(
        self,
        ticker: str,
        timeframe_days: int = 30,
        include_personal_context: bool = False,
    ) -> Outlook:
        """
        Generate an outlook for a given ticker.

        Args:
            ticker: Stock/ETF ticker symbol.
            timeframe_days: Outlook window in days.
            include_personal_context: Whether to include personalized context.

        Returns:
            Structured Outlook with descriptive metrics.
        """
        ticker = ticker.upper()
        logger.info(f"Generating {timeframe_days}-day outlook for {ticker}")

        # Get metadata (or use defaults)
        metadata = self._TICKER_METADATA.get(
            ticker,
            {"sector": "Broad Market", "base_volatility": 0.08, "historical_up_rate": 0.55},
        )

        sector = metadata["sector"]
        sector_trend = self._SECTOR_TRENDS.get(sector, (SentimentSummary.MIXED, 0.50))
        sector_momentum, sector_strength = sector_trend

        # Calculate sentiment
        sentiment = self._calculate_sentiment(
            sector_momentum=sector_momentum,
            sector_strength=sector_strength,
            historical_up_rate=metadata["historical_up_rate"],
        )

        # Select key drivers
        drivers = self._select_key_drivers(sector, sentiment)

        # Calculate volatility band
        volatility_band = self._calculate_volatility_band(
            base_volatility=metadata["base_volatility"],
            timeframe_days=timeframe_days,
            sector_strength=sector_strength,
        )

        # Adjust historical hit rate
        hit_rate = self._adjust_historical_rate(
            base_rate=metadata["historical_up_rate"],
            sentiment=sentiment,
            sector_strength=sector_strength,
        )

        return Outlook(
            ticker=ticker,
            timeframe_days=timeframe_days,
            sentiment_summary=sentiment,
            key_drivers=drivers,
            volatility_band=volatility_band,
            historical_hit_rate=hit_rate,
            personal_context=None,  # TODO: Implement with user context
            volatility_warning=None,
            timeframe_note=None,
            generated_at=datetime.utcnow(),
        )

    def _calculate_sentiment(
        self,
        sector_momentum: SentimentSummary,
        sector_strength: float,
        historical_up_rate: float,
    ) -> SentimentSummary:
        """Calculate overall sentiment from sector and ticker data."""
        combined_score = (sector_strength + historical_up_rate) / 2

        if sector_momentum == SentimentSummary.POSITIVE and combined_score > 0.55:
            return SentimentSummary.POSITIVE
        elif sector_momentum == SentimentSummary.CAUTIOUS and combined_score < 0.50:
            return SentimentSummary.CAUTIOUS
        else:
            return SentimentSummary.MIXED

    def _select_key_drivers(
        self,
        sector: str,
        sentiment: SentimentSummary,
    ) -> list[str]:
        """Select relevant key drivers based on sector and sentiment."""
        all_drivers = self._SECTOR_DRIVERS.get(
            sector,
            self._SECTOR_DRIVERS["Broad Market"],
        )

        # Select 3 random drivers
        selected = random.sample(all_drivers, min(3, len(all_drivers)))

        # Add a sentiment-appropriate driver
        sentiment_drivers = {
            SentimentSummary.POSITIVE: "Momentum indicators showing recent strength",
            SentimentSummary.CAUTIOUS: "Risk metrics elevated relative to recent history",
            SentimentSummary.MIXED: "Technical signals showing consolidation patterns",
        }
        selected.append(sentiment_drivers[sentiment])

        return selected

    def _calculate_volatility_band(
        self,
        base_volatility: float,
        timeframe_days: int,
        sector_strength: float,
    ) -> float:
        """Calculate expected volatility band."""
        import math

        # Volatility scales with square root of time
        time_adjustment = math.sqrt(timeframe_days / 30.0)

        # Sector weakness increases expected volatility
        sector_adjustment = 1.0 + (0.5 - sector_strength) * 0.3

        # Add some randomness for realism
        noise = random.uniform(0.95, 1.05)

        return round(base_volatility * time_adjustment * sector_adjustment * noise, 3)

    def _adjust_historical_rate(
        self,
        base_rate: float,
        sentiment: SentimentSummary,
        sector_strength: float,
    ) -> float:
        """Adjust historical hit rate based on current conditions."""
        adjusted = base_rate

        # Adjust based on sentiment
        if sentiment == SentimentSummary.POSITIVE:
            adjusted += 0.05
        elif sentiment == SentimentSummary.CAUTIOUS:
            adjusted -= 0.05

        # Factor in sector strength
        adjusted += (sector_strength - 0.5) * 0.1

        # Clamp to realistic range
        return round(min(0.80, max(0.35, adjusted)), 2)

