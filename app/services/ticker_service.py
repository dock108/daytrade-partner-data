"""
Ticker service — facade over canonical data providers.

Transforms provider data into API response models.
All raw data comes from app.providers (single source of truth).
"""

from app.core.logging import get_logger
from app.models.ticker import (
    ChartTimeRange,
    PriceHistory,
    PricePoint,
    TickerSnapshot,
    VolatilityLevel,
)
from app.providers.history_provider import HistoryProvider
from app.providers.price_provider import PriceProvider

logger = get_logger(__name__)


def _format_market_cap(market_cap: int | None) -> str:
    """Format market cap as human-readable string (e.g., 2.89T, 485B)."""
    if market_cap is None:
        return "N/A"
    if market_cap >= 1e12:
        return f"{market_cap / 1e12:.2f}T"
    if market_cap >= 1e9:
        return f"{market_cap / 1e9:.2f}B"
    if market_cap >= 1e6:
        return f"{market_cap / 1e6:.2f}M"
    return f"{market_cap:,.0f}"


def _calculate_volatility(week_52_high: float, week_52_low: float) -> VolatilityLevel:
    """Classify volatility based on 52-week price range."""
    if week_52_high <= 0 or week_52_low <= 0:
        return VolatilityLevel.MODERATE

    range_percent = (week_52_high - week_52_low) / week_52_low * 100

    if range_percent < 30:
        return VolatilityLevel.LOW
    elif range_percent < 60:
        return VolatilityLevel.MODERATE
    else:
        return VolatilityLevel.HIGH


# Company info cache (would come from a company data provider in production)
_COMPANY_INFO: dict[str, dict] = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "summary": "Consumer electronics and software company known for iPhone, Mac, and services ecosystem."},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "summary": "Leading designer of graphics processing units (GPUs) for gaming, data centers, and AI."},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "summary": "Enterprise software giant with cloud computing (Azure), productivity tools, and gaming."},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Communication Services", "summary": "Parent company of Google, leading in search, advertising, cloud computing, and AI."},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "summary": "E-commerce and cloud computing leader with AWS, retail, and streaming services."},
    "META": {"name": "Meta Platforms Inc.", "sector": "Communication Services", "summary": "Social media conglomerate operating Facebook, Instagram, WhatsApp, and Reality Labs."},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Discretionary", "summary": "Electric vehicle manufacturer and clean energy company with autonomous driving technology."},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "sector": "Broad Market", "summary": "Exchange-traded fund tracking the S&P 500 index."},
    "QQQ": {"name": "Invesco QQQ Trust", "sector": "Technology", "summary": "ETF tracking the Nasdaq-100 Index, focused on large-cap tech and growth stocks."},
    "AMD": {"name": "Advanced Micro Devices Inc.", "sector": "Technology", "summary": "Semiconductor company competing in CPUs, GPUs, and data center processors."},
}


class TickerService:
    """
    Service for ticker data — facade over canonical providers.

    All data comes from:
    - PriceProvider for current prices
    - HistoryProvider for historical data
    """

    def __init__(self):
        self._price_provider = PriceProvider()
        self._history_provider = HistoryProvider()

    async def get_snapshot(self, symbol: str) -> TickerSnapshot:
        """
        Get snapshot information for a ticker.

        Uses canonical PriceProvider for price data.
        """
        symbol = symbol.upper()
        logger.info(f"Fetching snapshot for {symbol}")

        # Get price from canonical provider
        price_data = await self._price_provider.get_price(symbol)

        # Get company info
        company = _COMPANY_INFO.get(symbol, {
            "name": symbol,
            "sector": "Unknown",
            "summary": f"{symbol} - market data",
        })

        # Calculate volatility from 52-week range
        volatility = _calculate_volatility(
            price_data.week_52_high,
            price_data.week_52_low,
        )

        return TickerSnapshot(
            ticker=symbol,
            company_name=company["name"],
            sector=company["sector"],
            market_cap=_format_market_cap(price_data.market_cap),
            volatility=volatility,
            summary=company["summary"],
            current_price=price_data.current_price,
            change_percent=price_data.change_percent,
            week_52_high=price_data.week_52_high,
            week_52_low=price_data.week_52_low,
            timestamp=price_data.timestamp,
            source=price_data.source,
        )

    async def get_history(
        self,
        symbol: str,
        time_range: ChartTimeRange = ChartTimeRange.ONE_MONTH,
    ) -> PriceHistory:
        """
        Get price history for a ticker.

        Uses canonical HistoryProvider for historical data.
        """
        symbol = symbol.upper()
        logger.info(f"Fetching {time_range.value} history for {symbol}")

        # Map ChartTimeRange to provider period
        period_map = {
            ChartTimeRange.ONE_DAY: "1D",
            ChartTimeRange.ONE_MONTH: "1M",
            ChartTimeRange.SIX_MONTHS: "6M",
            ChartTimeRange.ONE_YEAR: "1Y",
        }
        period = period_map.get(time_range, "1M")

        # Get history from canonical provider
        history_data = await self._history_provider.get_history(symbol, period)

        # Transform to API model
        points = [
            PricePoint(
                date=p.date,
                close=p.close,
                high=p.high,
                low=p.low,
            )
            for p in history_data.points
        ]

        return PriceHistory(
            ticker=symbol,
            points=points,
            current_price=history_data.end_price,
            change=history_data.change,
            change_percent=history_data.change_percent,
            timestamp=history_data.timestamp,
            source=history_data.source,
        )
