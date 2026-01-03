"""
Ticker data service.

Provides snapshot and historical price data, initially with mock data
and later integrated with yfinance.
"""

import random
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.errors import TickerNotFoundError
from app.core.logging import get_logger
from app.models.ticker import (
    ChartTimeRange,
    PriceHistory,
    PricePoint,
    TickerSnapshot,
    VolatilityLevel,
)

logger = get_logger(__name__)


class TickerService:
    """Service for fetching ticker snapshot and price history data."""

    # Mock ticker database
    _MOCK_TICKERS: dict[str, dict] = {
        "NVDA": {
            "company_name": "NVIDIA Corporation",
            "sector": "Technology",
            "market_cap": "1.22T",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Leading designer of graphics processing units (GPUs) for gaming, professional visualization, data centers, and automotive markets.",
            "base_price": 485.0,
        },
        "AAPL": {
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": "2.89T",
            "volatility": VolatilityLevel.LOW,
            "summary": "Consumer electronics and software company known for iPhone, Mac, and services ecosystem.",
            "base_price": 185.0,
        },
        "MSFT": {
            "company_name": "Microsoft Corporation",
            "sector": "Technology",
            "market_cap": "2.78T",
            "volatility": VolatilityLevel.LOW,
            "summary": "Enterprise software giant with cloud computing (Azure), productivity tools, and gaming divisions.",
            "base_price": 375.0,
        },
        "GOOGL": {
            "company_name": "Alphabet Inc.",
            "sector": "Communication Services",
            "market_cap": "1.75T",
            "volatility": VolatilityLevel.MODERATE,
            "summary": "Parent company of Google, leading in search, advertising, cloud computing, and AI research.",
            "base_price": 142.0,
        },
        "AMZN": {
            "company_name": "Amazon.com Inc.",
            "sector": "Consumer Discretionary",
            "market_cap": "1.55T",
            "volatility": VolatilityLevel.MODERATE,
            "summary": "E-commerce and cloud computing leader with AWS, retail, and streaming services.",
            "base_price": 155.0,
        },
        "META": {
            "company_name": "Meta Platforms Inc.",
            "sector": "Communication Services",
            "market_cap": "895B",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Social media conglomerate operating Facebook, Instagram, WhatsApp, and Reality Labs.",
            "base_price": 355.0,
        },
        "TSLA": {
            "company_name": "Tesla Inc.",
            "sector": "Consumer Discretionary",
            "market_cap": "785B",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Electric vehicle manufacturer and clean energy company with autonomous driving technology.",
            "base_price": 245.0,
        },
        "SPY": {
            "company_name": "SPDR S&P 500 ETF Trust",
            "sector": "Broad Market",
            "market_cap": "485B",
            "volatility": VolatilityLevel.LOW,
            "summary": "Exchange-traded fund tracking the S&P 500 index, providing broad market exposure.",
            "base_price": 475.0,
        },
        "QQQ": {
            "company_name": "Invesco QQQ Trust",
            "sector": "Technology",
            "market_cap": "195B",
            "volatility": VolatilityLevel.MODERATE,
            "summary": "ETF tracking the Nasdaq-100 Index, focused on large-cap tech and growth stocks.",
            "base_price": 405.0,
        },
        "AMD": {
            "company_name": "Advanced Micro Devices Inc.",
            "sector": "Technology",
            "market_cap": "225B",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Semiconductor company competing in CPUs, GPUs, and data center processors.",
            "base_price": 138.0,
        },
    }

    async def get_snapshot(self, symbol: str) -> TickerSnapshot:
        """
        Get snapshot information for a ticker.

        Args:
            symbol: Stock/ETF ticker symbol.

        Returns:
            TickerSnapshot with company info and metadata.

        Raises:
            TickerNotFoundError: If ticker is not found.
        """
        symbol = symbol.upper()
        logger.info(f"Fetching snapshot for {symbol}")

        if settings.USE_MOCK_DATA:
            return self._get_mock_snapshot(symbol)

        # TODO: Implement yfinance integration
        return self._get_mock_snapshot(symbol)

    async def get_history(
        self,
        symbol: str,
        time_range: ChartTimeRange = ChartTimeRange.ONE_MONTH,
    ) -> PriceHistory:
        """
        Get price history for a ticker.

        Args:
            symbol: Stock/ETF ticker symbol.
            time_range: Time range for historical data.

        Returns:
            PriceHistory with price points and change info.

        Raises:
            TickerNotFoundError: If ticker is not found.
        """
        symbol = symbol.upper()
        logger.info(f"Fetching {time_range.value} history for {symbol}")

        if settings.USE_MOCK_DATA:
            return self._get_mock_history(symbol, time_range)

        # TODO: Implement yfinance integration
        return self._get_mock_history(symbol, time_range)

    def _get_mock_snapshot(self, symbol: str) -> TickerSnapshot:
        """Generate mock snapshot data."""
        ticker_data = self._MOCK_TICKERS.get(symbol)

        if not ticker_data:
            raise TickerNotFoundError(symbol)

        return TickerSnapshot(
            ticker=symbol,
            company_name=ticker_data["company_name"],
            sector=ticker_data["sector"],
            market_cap=ticker_data["market_cap"],
            volatility=ticker_data["volatility"],
            summary=ticker_data["summary"],
        )

    def _get_mock_history(
        self,
        symbol: str,
        time_range: ChartTimeRange,
    ) -> PriceHistory:
        """Generate mock price history data."""
        ticker_data = self._MOCK_TICKERS.get(symbol)

        if not ticker_data:
            raise TickerNotFoundError(symbol)

        base_price = ticker_data["base_price"]
        volatility = ticker_data["volatility"]

        # Volatility multiplier for price swings
        vol_mult = {
            VolatilityLevel.LOW: 0.01,
            VolatilityLevel.MODERATE: 0.02,
            VolatilityLevel.HIGH: 0.04,
        }[volatility]

        # Generate price points
        num_points = min(time_range.days, 252)  # Max ~1 year of trading days
        points: list[PricePoint] = []
        current_price = base_price

        now = datetime.utcnow()
        for i in range(num_points, 0, -1):
            date = now - timedelta(days=i)

            # Random walk with slight upward drift
            daily_return = random.gauss(0.0003, vol_mult)
            current_price *= 1 + daily_return

            # Generate OHLC
            daily_vol = current_price * vol_mult * 0.5
            high = current_price + random.uniform(0, daily_vol)
            low = current_price - random.uniform(0, daily_vol)
            close = current_price

            points.append(
                PricePoint(
                    date=date,
                    close=round(close, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                )
            )

        # Calculate change from first point
        if points:
            first_close = points[0].close
            change = round(current_price - first_close, 2)
            change_percent = round((change / first_close) * 100, 2)
        else:
            change = 0.0
            change_percent = 0.0

        return PriceHistory(
            ticker=symbol,
            points=points,
            current_price=round(current_price, 2),
            change=change,
            change_percent=change_percent,
        )

