"""
Ticker data service.

Provides snapshot and historical price data using yfinance,
with fallback to mock data when USE_MOCK_DATA is enabled.
"""

import random
from datetime import datetime, timedelta, timezone

import yfinance as yf

from app.core.config import settings
from app.core.errors import ExternalServiceError, TickerNotFoundError
from app.core.logging import get_logger
from app.models.ticker import (
    ChartTimeRange,
    PriceHistory,
    PricePoint,
    TickerSnapshot,
    VolatilityLevel,
)

logger = get_logger(__name__)


def _format_market_cap(market_cap: int | float | None) -> str:
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


class TickerService:
    """Service for fetching ticker snapshot and price history data."""

    # Mock ticker database for fallback
    _MOCK_TICKERS: dict[str, dict] = {
        "NVDA": {
            "company_name": "NVIDIA Corporation",
            "sector": "Technology",
            "market_cap": "1.22T",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Leading designer of graphics processing units (GPUs) for gaming, "
                       "professional visualization, data centers, and automotive markets.",
            "base_price": 485.0,
        },
        "AAPL": {
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": "2.89T",
            "volatility": VolatilityLevel.LOW,
            "summary": "Consumer electronics and software company known for iPhone, Mac, "
                       "and services ecosystem.",
            "base_price": 185.0,
        },
        "MSFT": {
            "company_name": "Microsoft Corporation",
            "sector": "Technology",
            "market_cap": "2.78T",
            "volatility": VolatilityLevel.LOW,
            "summary": "Enterprise software giant with cloud computing (Azure), "
                       "productivity tools, and gaming divisions.",
            "base_price": 375.0,
        },
        "GOOGL": {
            "company_name": "Alphabet Inc.",
            "sector": "Communication Services",
            "market_cap": "1.75T",
            "volatility": VolatilityLevel.MODERATE,
            "summary": "Parent company of Google, leading in search, advertising, "
                       "cloud computing, and AI research.",
            "base_price": 142.0,
        },
        "AMZN": {
            "company_name": "Amazon.com Inc.",
            "sector": "Consumer Discretionary",
            "market_cap": "1.55T",
            "volatility": VolatilityLevel.MODERATE,
            "summary": "E-commerce and cloud computing leader with AWS, retail, "
                       "and streaming services.",
            "base_price": 155.0,
        },
        "META": {
            "company_name": "Meta Platforms Inc.",
            "sector": "Communication Services",
            "market_cap": "895B",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Social media conglomerate operating Facebook, Instagram, "
                       "WhatsApp, and Reality Labs.",
            "base_price": 355.0,
        },
        "TSLA": {
            "company_name": "Tesla Inc.",
            "sector": "Consumer Discretionary",
            "market_cap": "785B",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Electric vehicle manufacturer and clean energy company "
                       "with autonomous driving technology.",
            "base_price": 245.0,
        },
        "SPY": {
            "company_name": "SPDR S&P 500 ETF Trust",
            "sector": "Broad Market",
            "market_cap": "485B",
            "volatility": VolatilityLevel.LOW,
            "summary": "Exchange-traded fund tracking the S&P 500 index, "
                       "providing broad market exposure.",
            "base_price": 475.0,
        },
        "QQQ": {
            "company_name": "Invesco QQQ Trust",
            "sector": "Technology",
            "market_cap": "195B",
            "volatility": VolatilityLevel.MODERATE,
            "summary": "ETF tracking the Nasdaq-100 Index, focused on "
                       "large-cap tech and growth stocks.",
            "base_price": 405.0,
        },
        "AMD": {
            "company_name": "Advanced Micro Devices Inc.",
            "sector": "Technology",
            "market_cap": "225B",
            "volatility": VolatilityLevel.HIGH,
            "summary": "Semiconductor company competing in CPUs, GPUs, "
                       "and data center processors.",
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
            ExternalServiceError: If yfinance fails.
        """
        symbol = symbol.upper()
        logger.info(f"Fetching snapshot for {symbol}")

        if settings.USE_MOCK_DATA:
            return self._get_mock_snapshot(symbol)

        return self._get_yfinance_snapshot(symbol)

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
            ExternalServiceError: If yfinance fails.
        """
        symbol = symbol.upper()
        logger.info(f"Fetching {time_range.value} history for {symbol}")

        if settings.USE_MOCK_DATA:
            return self._get_mock_history(symbol, time_range)

        return self._get_yfinance_history(symbol, time_range)

    def _get_yfinance_snapshot(self, symbol: str) -> TickerSnapshot:
        """Fetch snapshot data from yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid data
            if not info or info.get("regularMarketPrice") is None:
                # Try to check if it's a valid symbol by looking at other fields
                if not info.get("longName") and not info.get("shortName"):
                    raise TickerNotFoundError(symbol)
            
            # Extract fields with fallbacks
            company_name = info.get("longName") or info.get("shortName") or symbol
            sector = info.get("sector") or info.get("quoteType", "Unknown")
            market_cap = _format_market_cap(info.get("marketCap"))
            
            current_price = info.get("regularMarketPrice") or info.get("previousClose")
            change_percent = info.get("regularMarketChangePercent")
            week_52_high = info.get("fiftyTwoWeekHigh")
            week_52_low = info.get("fiftyTwoWeekLow")
            
            # Calculate volatility from 52-week range
            volatility = VolatilityLevel.MODERATE
            if week_52_high and week_52_low:
                volatility = _calculate_volatility(week_52_high, week_52_low)
            
            # Build summary from available info
            summary = info.get("longBusinessSummary", "")
            if summary and len(summary) > 200:
                # Truncate to first sentence or 200 chars
                summary = summary[:200].rsplit(" ", 1)[0] + "..."
            elif not summary:
                summary = f"{company_name} - {sector}"
            
            return TickerSnapshot(
                ticker=symbol,
                company_name=company_name,
                sector=sector,
                market_cap=market_cap,
                volatility=volatility,
                summary=summary,
                current_price=round(current_price, 2) if current_price else None,
                change_percent=round(change_percent, 2) if change_percent else None,
                week_52_high=round(week_52_high, 2) if week_52_high else None,
                week_52_low=round(week_52_low, 2) if week_52_low else None,
            )
            
        except TickerNotFoundError:
            raise
        except Exception as e:
            # Log at debug level to avoid noise; error details stay server-side
            logger.debug(f"yfinance error for {symbol}: {e}")
            raise ExternalServiceError("yfinance", "Failed to fetch ticker data")

    def _get_yfinance_history(
        self,
        symbol: str,
        time_range: ChartTimeRange,
    ) -> PriceHistory:
        """Fetch price history from yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch history with appropriate period and interval
            hist = ticker.history(
                period=time_range.yfinance_period,
                interval=time_range.yfinance_interval,
            )
            
            if hist.empty:
                raise TickerNotFoundError(symbol)
            
            # Convert to price points with UTC timestamps
            points: list[PricePoint] = []
            for idx, row in hist.iterrows():
                # Convert index to UTC datetime
                if hasattr(idx, "tz_convert"):
                    dt = idx.tz_convert("UTC").to_pydatetime()
                elif hasattr(idx, "to_pydatetime"):
                    dt = idx.to_pydatetime()
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = datetime.fromisoformat(str(idx)).replace(tzinfo=timezone.utc)
                
                points.append(
                    PricePoint(
                        date=dt,
                        close=round(float(row["Close"]), 2),
                        high=round(float(row["High"]), 2),
                        low=round(float(row["Low"]), 2),
                    )
                )
            
            if not points:
                raise TickerNotFoundError(symbol)
            
            # Calculate change from first to last point
            first_close = points[0].close
            current_price = points[-1].close
            change = round(current_price - first_close, 2)
            change_percent = round((change / first_close) * 100, 2) if first_close else 0.0
            
            return PriceHistory(
                ticker=symbol,
                points=points,
                current_price=current_price,
                change=change,
                change_percent=change_percent,
            )
            
        except TickerNotFoundError:
            raise
        except Exception as e:
            # Log at debug level to avoid noise; error details stay server-side
            logger.debug(f"yfinance history error for {symbol}: {e}")
            raise ExternalServiceError("yfinance", "Failed to fetch price history")

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
            current_price=ticker_data["base_price"],
            change_percent=round(random.uniform(-2, 2), 2),
            week_52_high=round(ticker_data["base_price"] * 1.25, 2),
            week_52_low=round(ticker_data["base_price"] * 0.75, 2),
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

        now = datetime.now(timezone.utc)
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
