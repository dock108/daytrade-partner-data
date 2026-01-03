"""
Tests for OutlookEngine core math computations.

Uses synthetic price series to verify statistical calculations
without depending on external data sources.
"""

import numpy as np
import pytest

from app.services.outlook_engine import (
    OutlookEngine,
    _classify_volatility,
    _determine_sentiment,
)
from app.models.outlook import SentimentSummary


class TestVolatilityClassification:
    """Tests for volatility classification logic."""

    def test_low_volatility(self):
        """Annualized std < 20% should be classified as low."""
        assert _classify_volatility(0.15) == "low"
        assert _classify_volatility(0.10) == "low"
        assert _classify_volatility(0.05) == "low"

    def test_moderate_volatility(self):
        """Annualized std 20-40% should be classified as moderate."""
        assert _classify_volatility(0.25) == "moderate"
        assert _classify_volatility(0.30) == "moderate"
        assert _classify_volatility(0.35) == "moderate"

    def test_high_volatility(self):
        """Annualized std > 40% should be classified as high."""
        assert _classify_volatility(0.45) == "high"
        assert _classify_volatility(0.60) == "high"
        assert _classify_volatility(0.80) == "high"

    def test_boundary_values(self):
        """Test exact boundary values."""
        assert _classify_volatility(0.20) == "moderate"  # At boundary
        assert _classify_volatility(0.40) == "high"  # At boundary
        assert _classify_volatility(0.199) == "low"
        assert _classify_volatility(0.399) == "moderate"


class TestSentimentDetermination:
    """Tests for sentiment determination logic."""

    def test_positive_sentiment(self):
        """High hit rate + positive recent return = positive."""
        assert _determine_sentiment(0.60, 0.05) == SentimentSummary.POSITIVE
        assert _determine_sentiment(0.70, 0.10) == SentimentSummary.POSITIVE
        assert _determine_sentiment(0.56, 0.01) == SentimentSummary.POSITIVE

    def test_cautious_sentiment_low_hit_rate(self):
        """Low hit rate = cautious."""
        assert _determine_sentiment(0.40, 0.05) == SentimentSummary.CAUTIOUS
        assert _determine_sentiment(0.35, 0.02) == SentimentSummary.CAUTIOUS

    def test_cautious_sentiment_negative_return(self):
        """Very negative recent return = cautious."""
        assert _determine_sentiment(0.60, -0.15) == SentimentSummary.CAUTIOUS
        assert _determine_sentiment(0.55, -0.12) == SentimentSummary.CAUTIOUS

    def test_mixed_sentiment(self):
        """Middle ground = mixed."""
        assert _determine_sentiment(0.50, 0.02) == SentimentSummary.MIXED
        assert _determine_sentiment(0.55, -0.05) == SentimentSummary.MIXED
        assert _determine_sentiment(0.48, 0.05) == SentimentSummary.MIXED


class TestRollingReturnsComputation:
    """Tests for rolling returns computation."""

    @pytest.fixture
    def engine(self):
        """Create OutlookEngine instance."""
        return OutlookEngine()

    def test_rolling_returns_basic(self, engine):
        """Test basic rolling return calculation."""
        # Simple price series: 100, 110, 121 (10% daily returns)
        closes = np.array([100.0, 110.0, 121.0, 133.1])
        
        # Rolling 1-day returns
        returns = engine._compute_rolling_returns(closes, window=1)
        
        # Each return should be ~10%
        assert len(returns) == 3
        np.testing.assert_almost_equal(returns[0], 0.10, decimal=2)
        np.testing.assert_almost_equal(returns[1], 0.10, decimal=2)

    def test_rolling_returns_longer_window(self, engine):
        """Test rolling returns with longer window."""
        # Prices: 100, 105, 110, 115, 120
        closes = np.array([100.0, 105.0, 110.0, 115.0, 120.0])
        
        # Rolling 2-day returns
        returns = engine._compute_rolling_returns(closes, window=2)
        
        # First return: (110 - 100) / 100 = 0.10
        # Second return: (115 - 105) / 105 ≈ 0.095
        # Third return: (120 - 110) / 110 ≈ 0.091
        assert len(returns) == 3
        np.testing.assert_almost_equal(returns[0], 0.10, decimal=2)

    def test_rolling_returns_empty_if_insufficient_data(self, engine):
        """Return empty array if not enough data for window."""
        closes = np.array([100.0, 105.0])
        returns = engine._compute_rolling_returns(closes, window=5)
        assert len(returns) == 0

    def test_rolling_returns_negative(self, engine):
        """Test with declining prices."""
        closes = np.array([100.0, 90.0, 81.0])  # 10% daily loss
        returns = engine._compute_rolling_returns(closes, window=1)
        
        assert len(returns) == 2
        np.testing.assert_almost_equal(returns[0], -0.10, decimal=2)


class TestRecentReturnComputation:
    """Tests for recent return computation."""

    @pytest.fixture
    def engine(self):
        """Create OutlookEngine instance."""
        return OutlookEngine()

    def test_recent_return_basic(self, engine):
        """Test basic recent return calculation."""
        closes = np.array([100.0, 105.0, 110.0, 115.0, 120.0])
        
        # 3-day return: (120 - 105) / 105 ≈ 14.3%
        result = engine._compute_recent_return(closes, days=3)
        np.testing.assert_almost_equal(result, 0.143, decimal=2)

    def test_recent_return_full_period(self, engine):
        """Test return over full period."""
        closes = np.array([100.0, 120.0])  # 20% return
        result = engine._compute_recent_return(closes, days=1)
        np.testing.assert_almost_equal(result, 0.20, decimal=2)

    def test_recent_return_handles_short_data(self, engine):
        """Test with less data than requested days."""
        closes = np.array([100.0, 110.0])
        result = engine._compute_recent_return(closes, days=30)
        # Should use available data
        np.testing.assert_almost_equal(result, 0.10, decimal=2)


class TestHitRateComputation:
    """Tests for hit rate (fraction of positive windows) computation."""

    @pytest.fixture
    def engine(self):
        """Create OutlookEngine instance."""
        return OutlookEngine()

    def test_hit_rate_all_positive(self, engine):
        """All positive returns = 100% hit rate."""
        # Steadily increasing prices
        closes = np.array([100.0, 105.0, 110.0, 115.0, 120.0, 125.0])
        returns = engine._compute_rolling_returns(closes, window=1)
        hit_rate = float(np.mean(returns > 0))
        assert hit_rate == 1.0

    def test_hit_rate_all_negative(self, engine):
        """All negative returns = 0% hit rate."""
        # Steadily decreasing prices
        closes = np.array([100.0, 95.0, 90.0, 85.0, 80.0, 75.0])
        returns = engine._compute_rolling_returns(closes, window=1)
        hit_rate = float(np.mean(returns > 0))
        assert hit_rate == 0.0

    def test_hit_rate_mixed(self, engine):
        """Mixed returns = partial hit rate."""
        # Alternating up/down
        closes = np.array([100.0, 110.0, 100.0, 110.0, 100.0])
        returns = engine._compute_rolling_returns(closes, window=1)
        hit_rate = float(np.mean(returns > 0))
        assert hit_rate == 0.5


class TestVolatilityBandComputation:
    """Tests for volatility band (std dev) computation."""

    @pytest.fixture
    def engine(self):
        """Create OutlookEngine instance."""
        return OutlookEngine()

    def test_volatility_band_constant_prices(self, engine):
        """Constant prices = zero volatility."""
        closes = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
        returns = engine._compute_rolling_returns(closes, window=1)
        std = float(np.std(returns))
        assert std == 0.0

    def test_volatility_band_volatile_prices(self, engine):
        """Large price swings = high volatility."""
        # 20% swings
        closes = np.array([100.0, 120.0, 96.0, 115.2, 92.16])
        returns = engine._compute_rolling_returns(closes, window=1)
        std = float(np.std(returns))
        assert std > 0.15  # Should be high


class TestKeyDriversGeneration:
    """Tests for key drivers generation."""

    @pytest.fixture
    def engine(self):
        """Create OutlookEngine instance."""
        return OutlookEngine()

    def test_key_drivers_always_present(self, engine):
        """Key drivers should always have at least 3 entries."""
        drivers = engine._build_key_drivers("low", SentimentSummary.POSITIVE)
        assert len(drivers) >= 3

    def test_key_drivers_include_volatility_context(self, engine):
        """High volatility should add volatility-specific driver."""
        drivers = engine._build_key_drivers("high", SentimentSummary.MIXED)
        driver_text = " ".join(drivers).lower()
        assert "volatility" in driver_text or "swings" in driver_text

    def test_key_drivers_include_sentiment_context(self, engine):
        """Sentiment should influence driver content."""
        positive_drivers = engine._build_key_drivers("moderate", SentimentSummary.POSITIVE)
        cautious_drivers = engine._build_key_drivers("moderate", SentimentSummary.CAUTIOUS)
        
        # Should have different content based on sentiment
        assert positive_drivers != cautious_drivers


class TestMockOutlookGeneration:
    """Integration tests for mock outlook generation."""

    @pytest.fixture
    def engine(self):
        """Create OutlookEngine with mock mode."""
        engine = OutlookEngine()
        engine._use_mock = True
        return engine

    @pytest.mark.asyncio
    async def test_mock_outlook_has_all_fields(self, engine):
        """Mock outlook should have all required fields."""
        outlook = await engine.compute_outlook("AAPL", 30)
        
        assert outlook.ticker == "AAPL"
        assert outlook.timeframe_days == 30
        assert outlook.sentiment_summary in list(SentimentSummary)
        assert len(outlook.key_drivers) >= 3
        assert 0 <= outlook.volatility_band <= 1
        assert 0 <= outlook.historical_hit_rate <= 1
        assert outlook.generated_at is not None

    @pytest.mark.asyncio
    async def test_mock_outlook_consistency(self, engine):
        """Known tickers should produce consistent values."""
        # Known ticker should have specific sentiment
        outlook1 = await engine.compute_outlook("AAPL", 30)
        outlook2 = await engine.compute_outlook("AAPL", 30)
        
        # Hit rate should be similar (within random variation)
        assert abs(outlook1.historical_hit_rate - outlook2.historical_hit_rate) < 0.10

    @pytest.mark.asyncio
    async def test_mock_outlook_unknown_ticker(self, engine):
        """Unknown tickers should still generate valid outlook."""
        outlook = await engine.compute_outlook("UNKNOWN123", 30)
        
        # Should still have all required fields
        assert outlook.ticker == "UNKNOWN123"
        assert len(outlook.key_drivers) >= 3

