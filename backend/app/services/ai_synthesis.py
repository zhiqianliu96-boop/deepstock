"""
AI Synthesis service for stock analysis.

Takes pre-computed pillar scores (fundamental, technical, sentiment) and raw
stock data, builds a structured prompt, and asks an AI provider to INTERPRET
the results — not recalculate them. Returns a structured analysis dict.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior equity analyst. All numerical scores and metrics below "
    "have been pre-computed quantitatively. Your job is to INTERPRET these "
    "numbers, NOT recalculate them. Provide actionable analysis."
)

RESPONSE_FORMAT_INSTRUCTION = """
Respond ONLY with valid JSON (no markdown, no commentary outside the JSON).
Use this exact schema:

{
  "verdict": "strong_buy" | "buy" | "hold" | "sell" | "strong_sell",
  "confidence": <float 0-1>,
  "summary": "<2-3 sentence executive summary>",
  "fundamental_interpretation": "<paragraph interpreting the fundamental data>",
  "technical_interpretation": "<paragraph interpreting the technical data>",
  "sentiment_interpretation": "<paragraph interpreting the sentiment data>",
  "risks": ["<risk 1>", "<risk 2>", "<risk 3>", ...],
  "catalysts": ["<catalyst 1>", "<catalyst 2>", "<catalyst 3>", ...],
  "price_targets": {
    "support": <float or null>,
    "resistance": <float or null>,
    "fair_value_range": [<low>, <high>] or null
  },
  "position_advice": "<paragraph with entry/exit suggestions>",
  "time_horizon": "short_term" | "medium_term" | "long_term",
  "dashboard": {
    "bias_check": "safe" | "caution" | "danger",
    "ma_alignment": "<bullish/bearish/transitional + brief reason>",
    "chip_health": "<healthy/weak/unavailable + reason>",
    "volume_signal": "<what volume tells us>",
    "action_checklist": ["Trend alignment: ...", "Bias rate: ...", "Volume: ...", "News: ..."],
    "news_digest": "<2-3 sentence summary of key news>"
  }
}
"""


def _safe_get(obj, *keys, default=None):
    """Safely traverse nested dicts/objects to get a value."""
    current = obj
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key, default)
        elif hasattr(current, key):
            current = getattr(current, key, default)
        else:
            return default
    return current


def _to_dict(obj):
    """Convert a dataclass or dict-like object to a plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    try:
        return asdict(obj)
    except (TypeError, AttributeError):
        # Not a dataclass; try __dict__
        if hasattr(obj, "__dict__"):
            return vars(obj)
        return {}


class AISynthesizer:
    """Synthesizes pre-computed stock analysis scores using an AI provider."""

    def _build_prompt(
        self,
        fundamental_score,
        technical_score,
        sentiment_score,
        stock_data,
        composite_score: float,
        lang: str | None = None,
    ) -> str:
        """Build the analysis prompt from scores and stock data."""
        fund_dict = _to_dict(fundamental_score)
        tech_dict = _to_dict(technical_score)
        sent_dict = _to_dict(sentiment_score)
        data_dict = _to_dict(stock_data)

        # --- Stock basic info ---
        stock_info = (
            f"Stock Code: {data_dict.get('code', 'N/A')}\n"
            f"Stock Name: {data_dict.get('name', 'N/A')}\n"
            f"Market: {data_dict.get('market', 'N/A')}\n"
            f"Sector: {data_dict.get('sector', 'N/A')}\n"
        )

        # --- Real-Time Quote (1.1) ---
        realtime_section = ""
        rt = data_dict.get("realtime_quote", {})
        if rt and isinstance(rt, dict):
            rt_lines = []
            label_map = {
                "price": "Current Price", "pe": "P/E (TTM)", "forward_pe": "Forward P/E",
                "pb": "P/B", "ps": "P/S", "market_cap": "Market Cap",
                "float_cap": "Float Cap", "volume": "Volume", "avg_volume": "Avg Volume",
                "turnover": "Turnover", "turnover_rate": "Turnover Rate",
                "high": "Day High", "low": "Day Low",
                "52w_high": "52W High", "52w_low": "52W Low",
                "beta": "Beta", "dividend_yield": "Dividend Yield",
            }
            for key, label in label_map.items():
                val = rt.get(key)
                if val is not None:
                    rt_lines.append(f"  - {label}: {val}")
            if rt_lines:
                realtime_section = "Real-Time Quote:\n" + "\n".join(rt_lines) + "\n"

        # --- Fundamental ---
        fundamentals_section = (
            f"Fundamental Score (total): {fund_dict.get('total', 'N/A')}/100\n"
            f"  Valuation: {fund_dict.get('valuation_score', 'N/A')}/25\n"
            f"  Profitability: {fund_dict.get('profitability_score', 'N/A')}/25\n"
            f"  Growth: {fund_dict.get('growth_score', 'N/A')}/25\n"
            f"  Financial Health: {fund_dict.get('health_score', 'N/A')}/25\n"
        )

        metrics = fund_dict.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = _to_dict(metrics)
        metrics_lines = []
        for key in ["pe", "pb", "ps", "peg", "roe", "roa", "gross_margin", "net_margin",
                     "operating_margin", "revenue_growth_yoy", "profit_growth_yoy",
                     "debt_to_equity", "current_ratio", "fcf_yield", "dividend_yield"]:
            val = metrics.get(key)
            if val is not None:
                metrics_lines.append(f"  - {key}: {val}")
        key_metrics_section = "Key Financial Metrics:\n" + "\n".join(
            metrics_lines if metrics_lines else ["  (no detailed metrics available)"]
        )

        # --- Technical ---
        technical_section = (
            f"Technical Score (total): {tech_dict.get('total', 'N/A')}/100\n"
            f"  Trend: {tech_dict.get('trend_score', 'N/A')}/30\n"
            f"  Momentum: {tech_dict.get('momentum_score', 'N/A')}/20\n"
            f"  Volume: {tech_dict.get('volume_score', 'N/A')}/20\n"
            f"  Structure: {tech_dict.get('structure_score', 'N/A')}/15\n"
            f"  Pattern: {tech_dict.get('pattern_score', 'N/A')}/15\n"
        )

        indicators = tech_dict.get("indicators", {})
        if not isinstance(indicators, dict):
            indicators = _to_dict(indicators)
        ind_lines = "\n".join(f"  - {k}: {v}" for k, v in indicators.items() if v is not None)
        if ind_lines:
            technical_section += f"Indicators:\n{ind_lines}\n"

        patterns = tech_dict.get("patterns", [])
        if patterns:
            technical_section += f"Patterns Detected: {patterns}\n"

        sr = tech_dict.get("support_resistance", {})
        if isinstance(sr, dict) and sr.get("levels"):
            technical_section += f"S/R Levels: {sr['levels'][:6]}\n"

        # --- Chip Distribution (1.2 — CN only) ---
        chip_section = ""
        chip_data = tech_dict.get("chip_data", {})
        if chip_data and isinstance(chip_data, dict):
            chip_lines = []
            chip_label_map = {
                "profit_ratio": "Profit Ratio",
                "avg_cost": "Avg Cost",
                "concentration": "Concentration",
                "health": "Chip Health",
            }
            for key, label in chip_label_map.items():
                val = chip_data.get(key)
                if val is not None:
                    chip_lines.append(f"  - {label}: {val}")
            if chip_lines:
                chip_section = "Chip Distribution (CN):\n" + "\n".join(chip_lines) + "\n"

        # --- Sentiment ---
        sentiment_section = (
            f"Sentiment Score (total): {sent_dict.get('total', 'N/A')}/100\n"
            f"  News Sentiment: {sent_dict.get('news_sentiment_score', 'N/A')}/40\n"
            f"  Event Impact: {sent_dict.get('event_impact_score', 'N/A')}/30\n"
            f"  Market Attention: {sent_dict.get('market_attention_score', 'N/A')}/15\n"
            f"  Source Quality: {sent_dict.get('source_quality_score', 'N/A')}/15\n"
        )

        cat_summary = sent_dict.get("category_summary", {})
        if cat_summary:
            sentiment_section += "News Categories: " + str(cat_summary) + "\n"

        articles = sent_dict.get("articles", [])
        sentiment_section += f"Article Count: {len(articles)}\n"

        # --- Top News Headlines (1.3) ---
        news_headlines_section = ""
        if articles:
            headline_lines = []
            for article in articles[:8]:
                title = article.get("title", "")
                if not title:
                    continue
                score = article.get("score", 0)
                if score > 0.1:
                    label = "[+]"
                elif score < -0.1:
                    label = "[-]"
                else:
                    label = "[~]"
                headline_lines.append(f"  {label} {title}")
            if headline_lines:
                news_headlines_section = (
                    "Top News Headlines (+ positive, ~ neutral, - negative):\n"
                    + "\n".join(headline_lines)
                    + "\n"
                )

        # --- Trading Context (1.4) ---
        trading_context_section = self._build_trading_context(data_dict, indicators)

        # --- Assemble ---
        lang_instruction = ""
        if lang and lang.startswith("zh"):
            lang_instruction = (
                "\n=== LANGUAGE ===\n"
                "You MUST write ALL text values in the JSON response in Chinese (简体中文). "
                "This includes: summary, fundamental_interpretation, technical_interpretation, "
                "sentiment_interpretation, risks, catalysts, position_advice, and ALL dashboard fields. "
                "Only the JSON keys and verdict/enum values should remain in English.\n"
            )

        prompt = (
            "=== STOCK ANALYSIS DATA ===\n\n"
            f"--- Stock Info ---\n{stock_info}\n"
            f"{realtime_section}\n"
            f"--- Fundamental Analysis ---\n{fundamentals_section}\n"
            f"{key_metrics_section}\n\n"
            f"--- Technical Analysis ---\n{technical_section}\n"
            f"{chip_section}\n"
            f"{trading_context_section}\n"
            f"--- Sentiment Analysis ---\n{sentiment_section}\n"
            f"{news_headlines_section}\n"
            f"--- Composite Score ---\n{composite_score:.2f}/100\n\n"
            "=== INSTRUCTIONS ===\n"
            "Based on all the pre-computed scores and data above, provide your "
            "expert interpretation and actionable investment analysis.\n"
            "Include the 'dashboard' object with bias_check, ma_alignment, chip_health, "
            "volume_signal, action_checklist (4-6 items), and news_digest.\n\n"
            f"{RESPONSE_FORMAT_INSTRUCTION}"
            f"{lang_instruction}"
        )
        return prompt

    @staticmethod
    def _build_trading_context(data_dict: dict, indicators: dict) -> str:
        """Build trading context section: bias rate, MA alignment, volume signal."""
        lines = []

        # Bias rate from MA5
        price = None
        rt = data_dict.get("realtime_quote", {})
        if isinstance(rt, dict):
            price = rt.get("price")

        ma5 = indicators.get("ma5") or indicators.get("MA5")
        if price is not None and ma5 is not None:
            try:
                bias = (float(price) - float(ma5)) / float(ma5) * 100
                bias_status = "SAFE" if abs(bias) <= 5 else ("CAUTION" if abs(bias) <= 10 else "DANGER")
                lines.append(f"  - MA5 Bias Rate: {bias:.2f}% ({bias_status})")
            except (ValueError, ZeroDivisionError, TypeError):
                pass

        # MA alignment
        ma_values = {}
        for period in ["5", "10", "20", "60"]:
            key_variants = [f"ma{period}", f"MA{period}", f"ma_{period}"]
            for k in key_variants:
                val = indicators.get(k)
                if val is not None:
                    try:
                        ma_values[int(period)] = float(val)
                    except (ValueError, TypeError):
                        pass
                    break

        if len(ma_values) >= 3:
            sorted_periods = sorted(ma_values.keys())
            sorted_vals = [ma_values[p] for p in sorted_periods]
            if all(sorted_vals[i] >= sorted_vals[i + 1] for i in range(len(sorted_vals) - 1)):
                lines.append("  - MA Alignment: BULLISH (short > medium > long)")
            elif all(sorted_vals[i] <= sorted_vals[i + 1] for i in range(len(sorted_vals) - 1)):
                lines.append("  - MA Alignment: BEARISH (short < medium < long)")
            else:
                lines.append("  - MA Alignment: TRANSITIONAL (mixed)")

        # Volume signal
        vol_ratio = indicators.get("volume_ratio") or indicators.get("vol_ratio")
        if vol_ratio is not None:
            try:
                vr = float(vol_ratio)
                if vr > 2.0:
                    lines.append(f"  - Volume Signal: HEAVY ({vr:.1f}x avg) — high activity, watch for breakout/reversal")
                elif vr > 1.3:
                    lines.append(f"  - Volume Signal: ABOVE AVG ({vr:.1f}x avg) — moderate increase")
                elif vr < 0.5:
                    lines.append(f"  - Volume Signal: THIN ({vr:.1f}x avg) — low liquidity, caution")
                else:
                    lines.append(f"  - Volume Signal: NORMAL ({vr:.1f}x avg)")
            except (ValueError, TypeError):
                pass

        if lines:
            return "Trading Context:\n" + "\n".join(lines) + "\n"
        return ""

    def _parse_response(self, raw_text: str) -> dict:
        """Parse AI response as JSON, with fallback strategies."""
        # First try: direct JSON parse
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Second try: extract JSON from markdown code blocks
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # Third try: find the first { ... } block
        brace_match = re.search(r"\{[\s\S]*\}", raw_text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: return raw text wrapped in a structured dict
        logger.warning("Failed to parse AI response as JSON, using fallback")
        return {
            "verdict": "hold",
            "confidence": 0.5,
            "summary": raw_text[:1000],
            "fundamental_interpretation": "AI response could not be parsed as structured JSON.",
            "technical_interpretation": "AI response could not be parsed as structured JSON.",
            "sentiment_interpretation": "AI response could not be parsed as structured JSON.",
            "risks": ["Unable to parse structured risk factors from AI response"],
            "catalysts": ["Unable to parse structured catalysts from AI response"],
            "price_targets": {
                "support": None,
                "resistance": None,
                "fair_value_range": None,
            },
            "position_advice": "Review raw AI output for details.",
            "time_horizon": "medium_term",
            "_raw_response": raw_text,
        }

    async def synthesize(
        self,
        fundamental_score,
        technical_score,
        sentiment_score,
        stock_data,
        composite_score: float,
        ai_provider_name: str | None = None,
        lang: str | None = None,
    ) -> dict:
        """Run AI synthesis on pre-computed analysis scores.

        Args:
            fundamental_score: Fundamental analysis result (dataclass or dict).
            technical_score: Technical analysis result (dataclass or dict).
            sentiment_score: Sentiment analysis result (dataclass or dict).
            stock_data: Raw stock data object (dataclass or dict).
            composite_score: Pre-computed weighted composite score.
            ai_provider_name: AI provider to use (None for default).

        Returns:
            A dict with structured AI interpretation of the analysis.
        """
        from app.services.ai_provider import get_ai_provider

        prompt = self._build_prompt(
            fundamental_score,
            technical_score,
            sentiment_score,
            stock_data,
            composite_score,
            lang=lang,
        )

        try:
            provider = get_ai_provider(ai_provider_name)
            raw_response = await provider.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
            )
            result = self._parse_response(raw_response)
            logger.info(
                "AI synthesis complete — verdict=%s, confidence=%.2f",
                result.get("verdict", "unknown"),
                result.get("confidence", 0),
            )
            return result

        except Exception as e:
            logger.error("AI synthesis failed: %s", str(e), exc_info=True)
            return {
                "verdict": "hold",
                "confidence": 0.0,
                "summary": f"AI synthesis unavailable: {str(e)}",
                "fundamental_interpretation": "AI synthesis failed.",
                "technical_interpretation": "AI synthesis failed.",
                "sentiment_interpretation": "AI synthesis failed.",
                "risks": ["AI synthesis was unavailable for this analysis"],
                "catalysts": [],
                "price_targets": {
                    "support": None,
                    "resistance": None,
                    "fair_value_range": None,
                },
                "position_advice": "Manual review recommended due to AI synthesis failure.",
                "time_horizon": "medium_term",
                "_error": str(e),
            }
