"""
Technical analysis service.

Orchestrates all analyzers, computes a composite technical score (0-100), and
assembles chart data for frontend rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import numpy as np

from app.analyzers.technical_indicators import TechnicalIndicators
from app.analyzers.volume_analysis import VolumeAnalyzer
from app.analyzers.institutional_flow import InstitutionalFlowAnalyzer
from app.analyzers.support_resistance import SupportResistanceAnalyzer
from app.analyzers.chip_analysis import ChipAnalyzer
from app.analyzers.pattern_recognition import PatternRecognizer


# --------------------------------------------------------------------------- #
# Data class for the composite score
# --------------------------------------------------------------------------- #
@dataclass
class TechnicalScore:
    total: float                           # 0-100
    trend_score: float                     # 0-30
    momentum_score: float                  # 0-20
    volume_score: float                    # 0-20
    structure_score: float                 # 0-15
    pattern_score: float                   # 0-15
    breakdown: dict = field(default_factory=dict)
    indicators: dict = field(default_factory=dict)
    support_resistance: dict = field(default_factory=dict)
    institutional_flow: dict = field(default_factory=dict)
    chip_data: dict = field(default_factory=dict)
    patterns: list = field(default_factory=list)
    chart_data: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Service
# --------------------------------------------------------------------------- #
class TechnicalService:
    """Run all technical analyzers and produce a composite TechnicalScore."""

    def __init__(self) -> None:
        self._ti = TechnicalIndicators()
        self._vol = VolumeAnalyzer()
        self._flow = InstitutionalFlowAnalyzer()
        self._sr = SupportResistanceAnalyzer()
        self._chip = ChipAnalyzer()
        self._pattern = PatternRecognizer()

    # ------------------------------------------------------------------ #
    # public entry point
    # ------------------------------------------------------------------ #
    async def analyze(self, stock_data: Any) -> TechnicalScore:
        """
        Parameters
        ----------
        stock_data : app.services.data_fetcher.StockData
            Must expose at minimum:
                - daily_df : pd.DataFrame  (OHLCV with columns date/open/close/high/low/volume)
                - current_price : float
            Optional attributes (may be None):
                - fund_flow_df : pd.DataFrame | None
                - chip_df : pd.DataFrame | None
        """
        daily_df: pd.DataFrame = getattr(stock_data, "daily", None) or pd.DataFrame()
        fund_flow_df = getattr(stock_data, "fund_flow", None)
        chip_df = getattr(stock_data, "chip_data", None)
        # Extract current price from realtime_quote or last close
        quote = getattr(stock_data, "realtime_quote", {}) or {}
        current_price: float = float(quote.get("price", 0) or 0)
        if current_price == 0 and not daily_df.empty and "close" in daily_df.columns:
            current_price = float(daily_df["close"].iloc[-1])

        # --- Run analyzers ------------------------------------------------ #
        indicator_result = self._ti.compute(daily_df)
        volume_result = self._vol.analyze(daily_df)
        flow_result = self._flow.analyze(fund_flow_df)
        sr_result = self._sr.analyze(daily_df, current_price)
        chip_result = self._chip.analyze(chip_df, current_price)
        patterns = self._pattern.recognize(daily_df)

        enriched_df: pd.DataFrame = indicator_result.get("enriched_df", pd.DataFrame())

        # --- Scoring ------------------------------------------------------ #
        trend = self._score_trend(indicator_result, current_price)
        momentum = self._score_momentum(indicator_result)
        volume = self._score_volume(volume_result)
        structure = self._score_structure(sr_result, chip_result, current_price)
        pattern = self._score_pattern(patterns)

        total = trend["score"] + momentum["score"] + volume["score"] + structure["score"] + pattern["score"]
        total = max(0.0, min(100.0, total))

        # --- Chart data for frontend ------------------------------------- #
        chart_data = self._build_chart_data(enriched_df)

        return TechnicalScore(
            total=round(total, 2),
            trend_score=round(trend["score"], 2),
            momentum_score=round(momentum["score"], 2),
            volume_score=round(volume["score"], 2),
            structure_score=round(structure["score"], 2),
            pattern_score=round(pattern["score"], 2),
            breakdown={
                "trend": trend,
                "momentum": momentum,
                "volume": volume,
                "structure": structure,
                "pattern": pattern,
            },
            indicators=indicator_result,
            support_resistance=sr_result,
            institutional_flow=flow_result,
            chip_data=chip_result,
            patterns=patterns,
            chart_data=chart_data,
        )

    # ================================================================== #
    #  SCORING SUB-ROUTINES
    # ================================================================== #

    # ------------------------------------------------------------------ #
    # Trend score  (0 – 30)
    # ------------------------------------------------------------------ #
    def _score_trend(self, ind: dict, current_price: float) -> dict:
        score = 0.0
        reasons: list[str] = []

        ma_current = ind.get("ma", {}).get("current", {})

        ma20 = ma_current.get("ma20")
        ma60 = ma_current.get("ma60")

        # Price above MA20 and MA60 = bullish (+20), below all = bearish (5)
        if ma20 is not None and ma60 is not None:
            if current_price > ma20 and current_price > ma60:
                score += 20
                reasons.append("Price above MA20 and MA60 — bullish trend.")
            elif current_price < ma20 and current_price < ma60:
                score += 5
                reasons.append("Price below MA20 and MA60 — bearish trend.")
            else:
                score += 12
                reasons.append("Price between key moving averages — mixed trend.")
        else:
            score += 10
            reasons.append("Insufficient MA data for trend assessment.")

        # MA alignment: MA5 > MA10 > MA20 > MA60 = +10
        ma5 = ma_current.get("ma5")
        ma10 = ma_current.get("ma10")
        if all(v is not None for v in (ma5, ma10, ma20, ma60)):
            if ma5 > ma10 > ma20 > ma60:
                score += 10
                reasons.append("Perfect bullish MA alignment (MA5>MA10>MA20>MA60).")
            elif ma5 < ma10 < ma20 < ma60:
                score += 0
                reasons.append("Bearish MA alignment (MA5<MA10<MA20<MA60).")
            else:
                score += 5
                reasons.append("Partial MA alignment — transitional phase.")

        score = max(0.0, min(30.0, score))
        return {"score": score, "reasons": reasons}

    # ------------------------------------------------------------------ #
    # Momentum score  (0 – 20)
    # ------------------------------------------------------------------ #
    def _score_momentum(self, ind: dict) -> dict:
        score = 0.0
        reasons: list[str] = []

        # RSI contribution
        rsi = ind.get("rsi", {})
        rsi_val = rsi.get("value")
        if rsi_val is not None:
            if 40 <= rsi_val <= 60:
                score += 10
                reasons.append(f"RSI neutral ({rsi_val:.1f}) — balanced momentum.")
            elif rsi_val > 70:
                score += 5
                reasons.append(f"RSI overbought ({rsi_val:.1f}) — potential pullback.")
            elif rsi_val < 30:
                score += 8
                reasons.append(f"RSI oversold ({rsi_val:.1f}) — potential bounce.")
            elif 60 < rsi_val <= 70:
                score += 8
                reasons.append(f"RSI moderately high ({rsi_val:.1f}) — bullish momentum.")
            else:  # 30-40
                score += 7
                reasons.append(f"RSI moderately low ({rsi_val:.1f}) — weak momentum.")
        else:
            score += 5

        # MACD contribution
        macd = ind.get("macd", {})
        macd_signal = macd.get("signal", "neutral")
        if macd_signal == "bullish_cross":
            score += 5
            reasons.append("MACD bullish cross — momentum turning up.")
        elif macd_signal == "bearish_cross":
            score += 2
            reasons.append("MACD bearish cross — momentum turning down.")
        elif macd_signal == "above_zero":
            score += 4
            reasons.append("MACD above zero line — positive momentum.")
        elif macd_signal == "below_zero":
            score += 2
            reasons.append("MACD below zero line — negative momentum.")
        else:
            score += 3

        # KDJ contribution
        kdj = ind.get("kdj", {})
        kdj_signal = kdj.get("signal", "neutral")
        if "golden_cross" in kdj_signal:
            score += 5
            reasons.append("KDJ golden cross — short-term bullish.")
        elif "death_cross" in kdj_signal:
            score += 1
            reasons.append("KDJ death cross — short-term bearish.")
        else:
            score += 3

        score = max(0.0, min(20.0, score))
        return {"score": score, "reasons": reasons}

    # ------------------------------------------------------------------ #
    # Volume score  (0 – 20)
    # ------------------------------------------------------------------ #
    def _score_volume(self, vol: dict) -> dict:
        score = 10.0  # start at neutral
        reasons: list[str] = []

        # Divergence analysis
        divergences = vol.get("divergences", [])
        for div in divergences:
            div_type = div.get("type", "")
            if div_type == "confirmed_uptrend":
                score += 2
                reasons.append(f'{div["window"]}d: {div["description"]}')
            elif div_type == "bearish_divergence":
                score -= 2
                reasons.append(f'{div["window"]}d: {div["description"]}')
            elif div_type == "distribution":
                score -= 2
                reasons.append(f'{div["window"]}d: {div["description"]}')
            elif div_type == "selling_exhaustion":
                score += 1
                reasons.append(f'{div["window"]}d: {div["description"]}')

        # Volume ratio flag
        vr = vol.get("volume_ratio", {})
        flag = vr.get("flag", "")
        ratio = vr.get("ratio")
        if flag == "unusual_high" and ratio is not None:
            # Unusual volume — bonus if in an uptrend divergence context
            has_confirmed = any(d.get("type") == "confirmed_uptrend" for d in divergences)
            if has_confirmed:
                score += 3
                reasons.append(f"High volume ({ratio:.1f}x avg) supporting price move.")
            else:
                score += 1
                reasons.append(f"Unusual volume ({ratio:.1f}x avg) — needs directional confirmation.")
        elif flag == "thin":
            score -= 1
            reasons.append("Thin volume — low conviction.")

        # Volume trend
        vt = vol.get("volume_trend", {})
        trend = vt.get("trend", "")
        if trend == "expanding":
            score += 1
            reasons.append("Volume trend expanding (5d > 20d avg).")
        elif trend == "contracting":
            score -= 1
            reasons.append("Volume trend contracting.")

        score = max(0.0, min(20.0, score))
        return {"score": score, "reasons": reasons}

    # ------------------------------------------------------------------ #
    # Structure score  (0 – 15)
    # ------------------------------------------------------------------ #
    def _score_structure(self, sr: dict, chip: dict, current_price: float) -> dict:
        score = 7.0  # start at mid
        reasons: list[str] = []

        # Support/resistance proximity
        levels = sr.get("levels", [])
        supports = [lv for lv in levels if lv.get("role") == "support"]
        resistances = [lv for lv in levels if lv.get("role") == "resistance"]

        # Near strong support = bonus
        if supports:
            nearest_support = max(supports, key=lambda x: x["level"])
            dist = abs(nearest_support.get("distance_pct", 100))
            if dist < 3 and nearest_support.get("strength", 0) >= 2:
                score += 3
                reasons.append(
                    f"Price near strong support at {nearest_support['level']:.2f} "
                    f"(strength {nearest_support['strength']})."
                )
            elif dist < 5:
                score += 1
                reasons.append(f"Support level at {nearest_support['level']:.2f} ({dist:.1f}% away).")

        # Clear S/R framework (multiple levels identified)
        if len(levels) >= 4:
            score += 2
            reasons.append(f"Well-defined S/R framework ({len(levels)} levels identified).")

        # Chip health bonus
        chip_health = chip.get("health", "unavailable")
        if chip_health == "strong":
            score += 3
            reasons.append("Chip distribution healthy — strong holder base.")
        elif chip_health == "healthy":
            score += 2
            reasons.append("Chip distribution moderately healthy.")
        elif chip_health == "weak":
            score -= 1
            reasons.append("Chip distribution weak — potential selling pressure.")
        elif chip_health == "unhealthy":
            score -= 2
            reasons.append("Chip distribution unhealthy — high risk.")

        score = max(0.0, min(15.0, score))
        return {"score": score, "reasons": reasons}

    # ------------------------------------------------------------------ #
    # Pattern score  (0 – 15)
    # ------------------------------------------------------------------ #
    def _score_pattern(self, patterns: list[dict]) -> dict:
        score = 7.0  # neutral baseline
        reasons: list[str] = []

        if not patterns:
            reasons.append("No significant candlestick patterns detected.")
            return {"score": score, "reasons": reasons}

        bullish_count = 0
        bearish_count = 0

        for p in patterns:
            ptype = p.get("type", "neutral")
            reliability = p.get("reliability", "low")

            weight = {"high": 3, "medium": 2, "low": 1}.get(reliability, 1)

            if ptype == "bullish":
                bullish_count += 1
                score += weight
                reasons.append(f"Bullish: {p['pattern']} on {p['date']} ({reliability} reliability).")
            elif ptype == "bearish":
                bearish_count += 1
                score -= weight
                reasons.append(f"Bearish: {p['pattern']} on {p['date']} ({reliability} reliability).")

        # Multiple confirmation bonus / penalty
        if bullish_count >= 3:
            score += 2
            reasons.append(f"Multiple bullish confirmations ({bullish_count} patterns).")
        if bearish_count >= 3:
            score -= 2
            reasons.append(f"Multiple bearish signals ({bearish_count} patterns).")

        score = max(0.0, min(15.0, score))
        return {"score": score, "reasons": reasons}

    # ================================================================== #
    #  CHART DATA
    # ================================================================== #
    def _build_chart_data(self, df: pd.DataFrame) -> dict:
        """Build chart-ready data from the enriched DataFrame for frontend ECharts."""
        if df is None or df.empty:
            return {"ohlcv": [], "indicators": {}}

        # Limit to last 250 trading days for chart rendering
        chart_df = df.tail(250).copy()

        # Convert date column to string for JSON serialization
        if "date" in chart_df.columns:
            chart_df["date"] = chart_df["date"].astype(str)

        # OHLCV data
        ohlcv_cols = ["date", "open", "close", "high", "low", "volume"]
        available = [c for c in ohlcv_cols if c in chart_df.columns]
        ohlcv = chart_df[available].replace({np.nan: None}).to_dict(orient="records")

        # Indicator columns
        indicator_cols = [
            "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
            "macd_dif", "macd_dea", "macd_hist",
            "rsi",
            "kdj_k", "kdj_d", "kdj_j",
            "boll_upper", "boll_mid", "boll_lower",
        ]

        indicators: dict[str, list] = {}
        for col in indicator_cols:
            if col in chart_df.columns:
                indicators[col] = [
                    round(float(v), 4) if pd.notna(v) else None
                    for v in chart_df[col]
                ]

        dates = chart_df["date"].tolist() if "date" in chart_df.columns else []

        return {
            "dates": dates,
            "ohlcv": ohlcv,
            "indicators": indicators,
        }
