"""
AI explanation service using OpenAI.

Generates structured explanations for user queries about market topics.
All outputs are descriptive — no predictions or financial advice.
"""

import json
import re
from datetime import UTC, datetime

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.models.ai import AIResponse
from app.models.outlook import Outlook
from app.models.ticker import TickerSnapshot
from app.services.outlook_engine import OutlookEngine
from app.services.ticker_service import TickerService

logger = get_logger(__name__)

# System prompt for the AI - neutral, educational, no recommendations
SYSTEM_PROMPT = """You are a neutral market explainer for everyday investors.

TODAY'S DATE: {current_date}

CORE RULES:
- You NEVER say "buy", "sell", "you should", or make direct recommendations.
- You explain in calm, clear language what is happening and why.
- You describe historical patterns without predicting the future.
- You present both sides of any situation objectively.
- You avoid sensational language and hype.
- If you are unsure about something, say you are unsure — do not guess.

NEWS & RECENCY RULES:
- Prefer discussing events from the last 7 days when available.
- If no recent events, discuss broader trends from the last 30-60 days.
- Do NOT reference specific events older than 60 days.
- NEVER invent headlines, news stories, or specific events.
- NEVER fabricate earnings dates, CEO quotes, or analyst ratings.
- If nothing meaningful has happened recently, say:
  "There haven't been any major confirmed updates recently."

DATE AWARENESS:
- Today's date is {current_date}.
- Do not use exact dates unless explicitly provided in the context.
- Use relative timeframes like "recently", "in the past week", "over the last month".

{simple_mode_instruction}

Respond ONLY with a valid JSON object (no markdown, no code blocks) with these exact keys:
- whatsHappeningNow: A 2-3 sentence description of the current situation
- keyDrivers: An array of 3-4 key factors as strings
- riskVsOpportunity: A balanced 2-3 sentence perspective on both sides
- historicalBehavior: A 2-3 sentence description of how this has behaved historically
- simpleRecap: A single sentence summary in plain language

Example format:
{{"whatsHappeningNow": "...", "keyDrivers": ["...", "..."], "riskVsOpportunity": "...", "historicalBehavior": "...", "simpleRecap": "..."}}
"""

SIMPLE_MODE_INSTRUCTION = """When explaining:
- Use simple, everyday language
- Avoid financial jargon
- Keep sentences short and clear
- Explain as if speaking to someone new to investing"""

NORMAL_MODE_INSTRUCTION = (
    """You can use standard financial terminology that everyday investors would understand."""
)


def _build_context_message(
    question: str,
    snapshot: TickerSnapshot | None,
    outlook: Outlook | None,
) -> str:
    """Build the user message with context data."""
    parts = [f"User question: {question}"]

    if snapshot:
        # Ticker-specific mode: include company data
        parts.append(f"""
Ticker data for {snapshot.ticker}:
- Company: {snapshot.company_name}
- Sector: {snapshot.sector}
- Current price: ${snapshot.current_price or "N/A"}
- Change today: {snapshot.change_percent or "N/A"}%
- 52-week high: ${snapshot.week_52_high or "N/A"}
- 52-week low: ${snapshot.week_52_low or "N/A"}
- Market cap: {snapshot.market_cap}
- Volatility level: {snapshot.volatility}""")

        if outlook:
            parts.append(f"""
Historical analysis for {outlook.ticker} ({outlook.timeframe_days}-day windows):
- Historical hit rate: {outlook.historical_hit_rate:.0%} of periods were positive
- Typical range: ±{outlook.volatility_band:.1%}
- Sentiment based on patterns: {outlook.sentiment_summary.value}
- Key drivers: {", ".join(outlook.key_drivers[:3])}""")
    else:
        # Macro mode: no specific ticker, focus on broader market forces
        parts.append("""
Context: This is a MACRO question about general market conditions.
No specific ticker was provided, so focus on:
- Broad market trends and indices (S&P 500, Nasdaq, etc.)
- Federal Reserve policy and interest rates
- Economic indicators (inflation, employment, GDP)
- Sector rotation and market breadth
- Global economic and geopolitical factors

Do NOT make up specific stock prices or ticker data.
Focus on explaining high-level market dynamics.""")

    return "\n".join(parts)


def _coerce_json(text: str) -> str:
    """
    Attempt to fix common JSON issues.

    Handles:
    - Trailing commas
    - Single quotes instead of double quotes
    - Unquoted keys
    - Newlines in strings
    """
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Replace single quotes with double quotes (simple cases)
    # Only if not already using double quotes
    if "'" in text and '"' not in text:
        text = text.replace("'", '"')

    # Remove control characters that break JSON
    text = re.sub(r"[\x00-\x1f]", " ", text)

    return text


def _parse_ai_response(content: str) -> dict | None:
    """
    Parse AI response JSON with multiple fallback strategies.

    Tries:
    1. Direct JSON parse
    2. Extract from markdown code blocks
    3. Find JSON object pattern
    4. Coerce and retry each strategy
    """
    if not content:
        return None

    strategies = []

    # Strategy 1: Direct parse
    strategies.append(content.strip())

    # Strategy 2: Extract from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if json_match:
        strategies.append(json_match.group(1).strip())

    # Strategy 3: Find JSON object pattern
    json_match = re.search(r"\{[\s\S]*\}", content)
    if json_match:
        strategies.append(json_match.group(0).strip())

    # Try each strategy, then try with coercion
    for text in strategies:
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try with coercion
        try:
            coerced = _coerce_json(text)
            return json.loads(coerced)
        except json.JSONDecodeError:
            pass

    # All strategies failed
    logger.warning(f"All JSON parsing strategies failed for content: {content[:200]}...")
    return None


def _validate_response_keys(parsed: dict | None) -> bool:
    """Check if parsed response has all required keys."""
    if not parsed or not isinstance(parsed, dict):
        return False

    required_keys = [
        "whatsHappeningNow",
        "keyDrivers",
        "riskVsOpportunity",
        "historicalBehavior",
        "simpleRecap",
    ]
    return all(k in parsed for k in required_keys)


def _generate_fallback_response(
    question: str,
    symbol: str | None,
    snapshot: TickerSnapshot | None,
    outlook: Outlook | None,
) -> dict:
    """Generate a fallback response when AI parsing fails."""
    if symbol and snapshot:
        # Get volatility as string value
        vol_level = (
            snapshot.volatility.value
            if hasattr(snapshot.volatility, "value")
            else str(snapshot.volatility)
        )
        return {
            "whatsHappeningNow": (
                f"{symbol} is currently trading at ${snapshot.current_price or 'recent levels'}. "
                f"The stock has shown {vol_level} volatility recently, "
                f"within its 52-week range of ${snapshot.week_52_low} to ${snapshot.week_52_high}."
            ),
            "keyDrivers": [
                "Company earnings and guidance",
                "Sector-wide trends",
                "Broader market conditions",
                "Investor sentiment",
            ],
            "riskVsOpportunity": (
                f"Like any investment, {symbol} presents both potential opportunities and risks. "
                f"The {vol_level} volatility level suggests the typical range of price movements."
            ),
            "historicalBehavior": (
                f"Historically, {symbol} has shown patterns consistent with its sector. "
                f"Past performance varies based on market conditions and company-specific factors."
            )
            if not outlook
            else (
                f"Over {outlook.timeframe_days}-day periods, {symbol} has been positive "
                f"{outlook.historical_hit_rate:.0%} of the time, with typical swings of ±{outlook.volatility_band:.1%}."
            ),
            "simpleRecap": (
                f"{symbol} is showing {vol_level} volatility with multiple factors at play."
            ),
        }
    else:
        # Macro mode: high-level market explanation without ticker-specific data
        return {
            "whatsHappeningNow": (
                "Markets are navigating a complex environment shaped by monetary policy, "
                "economic data releases, and global events. Investor sentiment continues "
                "to react to shifts in inflation expectations and central bank guidance."
            ),
            "keyDrivers": [
                "Federal Reserve policy and interest rate trajectory",
                "Inflation data and economic growth indicators",
                "Corporate earnings trends across sectors",
                "Geopolitical developments and global trade dynamics",
                "Labor market conditions and consumer spending",
            ],
            "riskVsOpportunity": (
                "The current environment presents a mix of opportunities and risks. "
                "While economic resilience supports growth expectations, elevated rates "
                "and valuation concerns warrant a balanced perspective. Diversification "
                "remains a key consideration for managing uncertainty."
            ),
            "historicalBehavior": (
                "Markets have historically moved through cycles of expansion and contraction, "
                "often driven by shifts in monetary policy and economic conditions. "
                "Periods of volatility tend to create both challenges and opportunities "
                "for different investment approaches."
            ),
            "simpleRecap": (
                "Markets are balancing growth signals against rate and inflation concerns, "
                "with multiple cross-currents affecting different sectors."
            ),
        }


class AIService:
    """Service for generating AI-powered market explanations."""

    def __init__(self):
        self._client = (
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        )
        self._ticker_service = TickerService()
        self._outlook_engine = OutlookEngine()

    async def generate_explanation(
        self,
        question: str,
        symbol: str | None = None,
        timeframe_days: int | None = None,
        simple_mode: bool = False,
    ) -> AIResponse:
        """
        Generate a structured explanation for a market question.

        Args:
            question: User's question about the market/ticker.
            symbol: Optional ticker symbol for context.
            timeframe_days: Optional timeframe for outlook (default 30).
            simple_mode: Whether to use simpler language.

        Returns:
            AIResponse with 5 structured explanation fields.
        """
        logger.info(f"Generating explanation for: {question[:50]}...")

        # Normalize symbol
        symbol = symbol.upper().strip() if symbol else None
        timeframe_days = timeframe_days or 30

        # Fetch context data if symbol provided
        snapshot: TickerSnapshot | None = None
        outlook: Outlook | None = None

        if symbol:
            try:
                snapshot = await self._ticker_service.get_snapshot(symbol)
            except Exception as e:
                logger.debug(f"Could not fetch snapshot for {symbol}: {e}")

            try:
                outlook = await self._outlook_engine.compute_outlook(symbol, timeframe_days)
            except Exception as e:
                logger.debug(f"Could not fetch outlook for {symbol}: {e}")

        # Generate explanation
        if settings.USE_MOCK_DATA or not self._client:
            response_data = _generate_fallback_response(question, symbol, snapshot, outlook)
        else:
            response_data = await self._call_openai(
                question, symbol, snapshot, outlook, simple_mode
            )

        return AIResponse(
            whats_happening_now=response_data.get("whatsHappeningNow", ""),
            key_drivers=response_data.get("keyDrivers", []),
            risk_vs_opportunity=response_data.get("riskVsOpportunity", ""),
            historical_behavior=response_data.get("historicalBehavior", ""),
            simple_recap=response_data.get("simpleRecap", ""),
        )

    async def _call_openai(
        self,
        question: str,
        symbol: str | None,
        snapshot: TickerSnapshot | None,
        outlook: Outlook | None,
        simple_mode: bool,
        max_retries: int = 2,
    ) -> dict:
        """
        Call OpenAI API and parse response with retry logic.

        Args:
            max_retries: Number of attempts (default 2: initial + 1 retry)
        """
        # Build prompts with dynamic date
        mode_instruction = SIMPLE_MODE_INSTRUCTION if simple_mode else NORMAL_MODE_INSTRUCTION
        current_date = datetime.now(UTC).strftime("%B %d, %Y")
        system_prompt = SYSTEM_PROMPT.format(
            current_date=current_date,
            simple_mode_instruction=mode_instruction,
        )
        user_message = _build_context_message(question, snapshot, outlook)

        last_error: Exception | None = None
        last_content: str | None = None

        for attempt in range(max_retries):
            try:
                # Call OpenAI
                response = await self._client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7 if attempt == 0 else 0.5,  # Lower temp on retry
                    max_tokens=1000,
                )

                content = response.choices[0].message.content
                last_content = content
                logger.debug(f"OpenAI response (attempt {attempt + 1}): {content[:200]}...")

                # Parse response
                parsed = _parse_ai_response(content)

                if _validate_response_keys(parsed):
                    return parsed

                # Parsing failed, will retry if attempts remain
                if attempt < max_retries - 1:
                    logger.info(f"JSON parsing failed, retrying (attempt {attempt + 2})...")

            except Exception as e:
                last_error = e
                logger.warning(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue

        # All retries exhausted - log details and return fallback
        if last_error:
            logger.error(f"OpenAI failed after {max_retries} attempts: {last_error}")
        elif last_content:
            logger.warning(
                f"JSON parsing failed after {max_retries} attempts. "
                f"Last response: {last_content[:300]}..."
            )

        return _generate_fallback_response(question, symbol, snapshot, outlook)
