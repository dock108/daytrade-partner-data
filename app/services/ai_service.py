"""
AI explanation service using OpenAI.

Generates structured explanations for user queries about market topics.
All outputs are descriptive — no predictions or financial advice.
"""

import json
import re
from datetime import datetime, timezone

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.errors import ExternalServiceError
from app.core.logging import get_logger
from app.models.explain import AIResponse, ExplainRequest
from app.models.outlook import Outlook
from app.models.ticker import TickerSnapshot
from app.services.outlook_engine import OutlookEngine
from app.services.ticker_service import TickerService

logger = get_logger(__name__)

# System prompt for the AI - neutral, educational, no recommendations
SYSTEM_PROMPT = """You are a neutral market explainer for everyday investors.

RULES:
- You NEVER say "buy", "sell", "you should", or make direct recommendations.
- You explain in calm, clear language what is happening and why.
- You describe historical patterns without predicting the future.
- You present both sides of any situation objectively.
- You avoid sensational language and hype.

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

NORMAL_MODE_INSTRUCTION = """You can use standard financial terminology that everyday investors would understand."""


def _build_context_message(
    question: str,
    snapshot: TickerSnapshot | None,
    outlook: Outlook | None,
) -> str:
    """Build the user message with context data."""
    parts = [f"User question: {question}"]
    
    if snapshot:
        parts.append(f"""
Ticker data for {snapshot.ticker}:
- Company: {snapshot.company_name}
- Sector: {snapshot.sector}
- Current price: ${snapshot.current_price or 'N/A'}
- Change today: {snapshot.change_percent or 'N/A'}%
- 52-week high: ${snapshot.week_52_high or 'N/A'}
- 52-week low: ${snapshot.week_52_low or 'N/A'}
- Market cap: {snapshot.market_cap}
- Volatility level: {snapshot.volatility}""")
    
    if outlook:
        parts.append(f"""
Historical analysis for {outlook.ticker} ({outlook.timeframe_days}-day windows):
- Historical hit rate: {outlook.historical_hit_rate:.0%} of periods were positive
- Typical range: ±{outlook.volatility_band:.1%}
- Sentiment based on patterns: {outlook.sentiment_summary.value}
- Key drivers: {', '.join(outlook.key_drivers[:3])}""")
    
    return "\n".join(parts)


def _parse_ai_response(content: str) -> dict:
    """
    Parse AI response JSON with fallback handling.
    
    Tries multiple strategies to extract valid JSON from the response.
    """
    # Try direct JSON parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object pattern
    json_match = re.search(r"\{[\s\S]*\}", content)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Fallback: return None to trigger template response
    return None


def _generate_fallback_response(
    question: str,
    symbol: str | None,
    snapshot: TickerSnapshot | None,
    outlook: Outlook | None,
) -> dict:
    """Generate a fallback response when AI parsing fails."""
    if symbol and snapshot:
        # Get volatility as string value
        vol_level = snapshot.volatility.value if hasattr(snapshot.volatility, 'value') else str(snapshot.volatility)
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
            ) if not outlook else (
                f"Over {outlook.timeframe_days}-day periods, {symbol} has been positive "
                f"{outlook.historical_hit_rate:.0%} of the time, with typical swings of ±{outlook.volatility_band:.1%}."
            ),
            "simpleRecap": (
                f"{symbol} is showing {vol_level} volatility with multiple factors at play."
            ),
        }
    else:
        return {
            "whatsHappeningNow": (
                "Markets are influenced by a variety of factors including economic data, "
                "corporate earnings, and global events. Understanding these dynamics helps "
                "provide context for investment decisions."
            ),
            "keyDrivers": [
                "Economic indicators and Fed policy",
                "Corporate earnings trends",
                "Global market conditions",
                "Sector rotation patterns",
            ],
            "riskVsOpportunity": (
                "Markets present both opportunities and risks. Diversification and "
                "understanding your own risk tolerance are key considerations."
            ),
            "historicalBehavior": (
                "Markets have historically gone through cycles of expansion and contraction. "
                "Long-term trends tend to reflect underlying economic fundamentals."
            ),
            "simpleRecap": (
                "Multiple factors are influencing markets right now, with both opportunities and risks present."
            ),
        }


class AIService:
    """Service for generating AI-powered market explanations."""

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
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
            response_data = await self._call_openai(question, symbol, snapshot, outlook, simple_mode)
        
        return AIResponse(
            question=question,
            symbol=symbol,
            whats_happening_now=response_data.get("whatsHappeningNow", ""),
            key_drivers=response_data.get("keyDrivers", []),
            risk_vs_opportunity=response_data.get("riskVsOpportunity", ""),
            historical_behavior=response_data.get("historicalBehavior", ""),
            simple_recap=response_data.get("simpleRecap", ""),
            generated_at=datetime.now(timezone.utc),
        )

    async def _call_openai(
        self,
        question: str,
        symbol: str | None,
        snapshot: TickerSnapshot | None,
        outlook: Outlook | None,
        simple_mode: bool,
    ) -> dict:
        """Call OpenAI API and parse response."""
        try:
            # Build prompts
            mode_instruction = SIMPLE_MODE_INSTRUCTION if simple_mode else NORMAL_MODE_INSTRUCTION
            system_prompt = SYSTEM_PROMPT.format(simple_mode_instruction=mode_instruction)
            user_message = _build_context_message(question, snapshot, outlook)
            
            # Call OpenAI
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content[:200]}...")
            
            # Parse response
            parsed = _parse_ai_response(content)
            
            if parsed and all(k in parsed for k in [
                "whatsHappeningNow", "keyDrivers", "riskVsOpportunity",
                "historicalBehavior", "simpleRecap"
            ]):
                return parsed
            
            # Fallback if parsing failed or missing keys
            logger.warning("OpenAI response parsing failed, using fallback")
            return _generate_fallback_response(question, symbol, snapshot, outlook)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Return fallback instead of raising to prevent 500s
            return _generate_fallback_response(question, symbol, snapshot, outlook)

