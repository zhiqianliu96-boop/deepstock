"""
Candlestick pattern recognition.

Pure computation — scans the last 10 trading days of a daily OHLCV DataFrame
for classical candlestick patterns.

Expected DataFrame columns: date, open, close, high, low, volume.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


class PatternRecognizer:
    """Detect candlestick patterns in recent price data."""

    SCAN_WINDOW = 10  # look at last N bars

    def recognize(self, df: pd.DataFrame) -> list[dict]:
        if df is None or df.empty:
            return []

        df = df.copy()
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        window = df.iloc[-self.SCAN_WINDOW:] if len(df) >= self.SCAN_WINDOW else df
        patterns: list[dict] = []

        for i in range(len(window)):
            row = window.iloc[i]
            prev = window.iloc[i - 1] if i > 0 else None
            prev2 = window.iloc[i - 2] if i > 1 else None

            patterns.extend(self._check_doji(row))
            patterns.extend(self._check_hammer(row))
            patterns.extend(self._check_inverted_hammer(row))

            if prev is not None:
                patterns.extend(self._check_engulfing(prev, row))
                patterns.extend(self._check_gap(prev, row))

            if prev is not None and prev2 is not None:
                patterns.extend(self._check_morning_star(prev2, prev, row))
                patterns.extend(self._check_evening_star(prev2, prev, row))

        # Sort by date descending
        patterns.sort(key=lambda p: str(p.get("date", "")), reverse=True)
        return patterns

    # ------------------------------------------------------------------ #
    # helpers: candle metrics
    # ------------------------------------------------------------------ #
    @staticmethod
    def _body(row: pd.Series) -> float:
        return abs(row["close"] - row["open"])

    @staticmethod
    def _range(row: pd.Series) -> float:
        return row["high"] - row["low"]

    @staticmethod
    def _upper_shadow(row: pd.Series) -> float:
        return row["high"] - max(row["open"], row["close"])

    @staticmethod
    def _lower_shadow(row: pd.Series) -> float:
        return min(row["open"], row["close"]) - row["low"]

    @staticmethod
    def _is_bullish(row: pd.Series) -> bool:
        return row["close"] >= row["open"]

    # ------------------------------------------------------------------ #
    # Doji: open ~ close within 0.1% of range
    # ------------------------------------------------------------------ #
    def _check_doji(self, row: pd.Series) -> list[dict]:
        rng = self._range(row)
        if rng == 0:
            return []
        body = self._body(row)
        if body / rng <= 0.1:
            return [{
                "date": str(row["date"]),
                "pattern": "doji",
                "type": "neutral",
                "reliability": "medium",
                "description": "Open and close nearly equal — market indecision.",
            }]
        return []

    # ------------------------------------------------------------------ #
    # Hammer: small body at top, long lower shadow (>2x body), little upper shadow
    # ------------------------------------------------------------------ #
    def _check_hammer(self, row: pd.Series) -> list[dict]:
        body = self._body(row)
        rng = self._range(row)
        if rng == 0 or body == 0:
            return []
        lower = self._lower_shadow(row)
        upper = self._upper_shadow(row)

        if lower >= 2.0 * body and upper <= body * 0.5:
            return [{
                "date": str(row["date"]),
                "pattern": "hammer",
                "type": "bullish",
                "reliability": "high",
                "description": "Small body at top with long lower shadow — potential bullish reversal.",
            }]
        return []

    # ------------------------------------------------------------------ #
    # Inverted Hammer: small body at bottom, long upper shadow
    # ------------------------------------------------------------------ #
    def _check_inverted_hammer(self, row: pd.Series) -> list[dict]:
        body = self._body(row)
        rng = self._range(row)
        if rng == 0 or body == 0:
            return []
        lower = self._lower_shadow(row)
        upper = self._upper_shadow(row)

        if upper >= 2.0 * body and lower <= body * 0.5:
            return [{
                "date": str(row["date"]),
                "pattern": "inverted_hammer",
                "type": "bullish",
                "reliability": "medium",
                "description": "Small body at bottom with long upper shadow — potential reversal.",
            }]
        return []

    # ------------------------------------------------------------------ #
    # Engulfing: current body completely engulfs previous body
    # ------------------------------------------------------------------ #
    def _check_engulfing(self, prev: pd.Series, curr: pd.Series) -> list[dict]:
        prev_body = self._body(prev)
        curr_body = self._body(curr)
        if prev_body == 0 or curr_body == 0:
            return []

        prev_open, prev_close = prev["open"], prev["close"]
        curr_open, curr_close = curr["open"], curr["close"]

        prev_top = max(prev_open, prev_close)
        prev_bot = min(prev_open, prev_close)
        curr_top = max(curr_open, curr_close)
        curr_bot = min(curr_open, curr_close)

        if curr_top > prev_top and curr_bot < prev_bot:
            # Bullish engulfing: previous was red, current is green
            if not self._is_bullish(prev) and self._is_bullish(curr):
                return [{
                    "date": str(curr["date"]),
                    "pattern": "bullish_engulfing",
                    "type": "bullish",
                    "reliability": "high",
                    "description": "Green candle engulfs previous red candle — bullish reversal signal.",
                }]
            # Bearish engulfing: previous was green, current is red
            elif self._is_bullish(prev) and not self._is_bullish(curr):
                return [{
                    "date": str(curr["date"]),
                    "pattern": "bearish_engulfing",
                    "type": "bearish",
                    "reliability": "high",
                    "description": "Red candle engulfs previous green candle — bearish reversal signal.",
                }]
        return []

    # ------------------------------------------------------------------ #
    # Morning Star: 3-candle bullish reversal
    # ------------------------------------------------------------------ #
    def _check_morning_star(
        self, first: pd.Series, second: pd.Series, third: pd.Series,
    ) -> list[dict]:
        first_body = self._body(first)
        second_body = self._body(second)
        third_body = self._body(third)
        first_range = self._range(first)

        if first_range == 0:
            return []

        # First: big red candle
        is_big_red = not self._is_bullish(first) and first_body / first_range > 0.5
        # Second: small body (star), gaps down
        is_small = second_body < first_body * 0.5
        gaps_down = max(second["open"], second["close"]) < min(first["open"], first["close"])
        # Third: big green candle, gaps up
        is_big_green = self._is_bullish(third) and third_body > first_body * 0.5
        gaps_up = min(third["open"], third["close"]) > max(second["open"], second["close"])

        # Relaxed check: require big red + small body + big green; gap is bonus
        if is_big_red and is_small and is_big_green:
            reliability = "high" if (gaps_down and gaps_up) else "medium"
            return [{
                "date": str(third["date"]),
                "pattern": "morning_star",
                "type": "bullish",
                "reliability": reliability,
                "description": "Three-candle bullish reversal: large red, small body, large green.",
            }]
        return []

    # ------------------------------------------------------------------ #
    # Evening Star: 3-candle bearish reversal
    # ------------------------------------------------------------------ #
    def _check_evening_star(
        self, first: pd.Series, second: pd.Series, third: pd.Series,
    ) -> list[dict]:
        first_body = self._body(first)
        second_body = self._body(second)
        third_body = self._body(third)
        first_range = self._range(first)

        if first_range == 0:
            return []

        # First: big green candle
        is_big_green = self._is_bullish(first) and first_body / first_range > 0.5
        # Second: small body (star), gaps up
        is_small = second_body < first_body * 0.5
        gaps_up = min(second["open"], second["close"]) > max(first["open"], first["close"])
        # Third: big red candle, gaps down
        is_big_red = not self._is_bullish(third) and third_body > first_body * 0.5
        gaps_down = max(third["open"], third["close"]) < min(second["open"], second["close"])

        if is_big_green and is_small and is_big_red:
            reliability = "high" if (gaps_up and gaps_down) else "medium"
            return [{
                "date": str(third["date"]),
                "pattern": "evening_star",
                "type": "bearish",
                "reliability": reliability,
                "description": "Three-candle bearish reversal: large green, small body, large red.",
            }]
        return []

    # ------------------------------------------------------------------ #
    # Gap up / down (>1% gap between previous close and current open)
    # ------------------------------------------------------------------ #
    def _check_gap(self, prev: pd.Series, curr: pd.Series) -> list[dict]:
        if prev["close"] == 0:
            return []
        gap_pct = (curr["open"] - prev["close"]) / prev["close"] * 100
        if gap_pct > 1.0:
            return [{
                "date": str(curr["date"]),
                "pattern": "gap_up",
                "type": "bullish",
                "reliability": "medium",
                "description": f"Gap up of {gap_pct:.2f}% — bullish momentum.",
            }]
        elif gap_pct < -1.0:
            return [{
                "date": str(curr["date"]),
                "pattern": "gap_down",
                "type": "bearish",
                "reliability": "medium",
                "description": f"Gap down of {abs(gap_pct):.2f}% — bearish pressure.",
            }]
        return []
