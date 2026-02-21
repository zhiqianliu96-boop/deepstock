"""
Support and resistance level detection.

Pure computation — takes a daily OHLCV DataFrame and the current price, then
returns a structured dict of support / resistance levels from multiple methods.

Expected DataFrame columns: date, open, close, high, low, volume.
"""

from __future__ import annotations

import math
from collections import defaultdict

import pandas as pd
import numpy as np


class SupportResistanceAnalyzer:
    """Identify support and resistance levels via multiple techniques."""

    FRACTAL_WINDOW = 5       # bars each side for fractal detection
    CLUSTER_PCT = 0.02       # 2% threshold to cluster nearby levels
    FRACTAL_LOOKBACK = 60    # look at last 60 bars for fractals

    def analyze(self, df: pd.DataFrame, current_price: float) -> dict:
        if df is None or df.empty or current_price is None:
            return self._empty_result()

        df = df.copy()
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        pivots = self._pivot_points(df)
        fractal_levels = self._fractal_levels(df)
        ma_levels = self._ma_levels(df)
        round_levels = self._round_number_levels(current_price)

        # Merge all raw levels, cluster, label, and score by strength.
        all_levels = self._merge_levels(
            pivots, fractal_levels, ma_levels, round_levels, current_price,
        )

        return {
            "pivot_points": pivots,
            "fractal_levels": fractal_levels,
            "ma_levels": ma_levels,
            "round_levels": round_levels,
            "levels": all_levels,
            "current_price": current_price,
        }

    # ------------------------------------------------------------------ #
    # Pivot Points (classic)
    # ------------------------------------------------------------------ #
    def _pivot_points(self, df: pd.DataFrame) -> dict:
        last = df.iloc[-1]
        h = float(last["high"])
        l = float(last["low"])
        c = float(last["close"])

        pp = (h + l + c) / 3.0
        r1 = 2.0 * pp - l
        s1 = 2.0 * pp - h
        r2 = pp + (h - l)
        s2 = pp - (h - l)

        return {
            "pp": round(pp, 4),
            "r1": round(r1, 4),
            "r2": round(r2, 4),
            "s1": round(s1, 4),
            "s2": round(s2, 4),
        }

    # ------------------------------------------------------------------ #
    # Fractal highs / lows
    # ------------------------------------------------------------------ #
    def _fractal_levels(self, df: pd.DataFrame) -> list[dict]:
        n = self.FRACTAL_WINDOW
        lookback = min(len(df), self.FRACTAL_LOOKBACK)
        window_df = df.iloc[-lookback:]
        fractals: list[dict] = []

        for i in range(n, len(window_df) - n):
            seg = window_df.iloc[i - n: i + n + 1]
            bar = window_df.iloc[i]

            # Fractal high
            if bar["high"] == seg["high"].max():
                fractals.append({
                    "level": round(float(bar["high"]), 4),
                    "type": "fractal_high",
                    "date": str(bar["date"]),
                })

            # Fractal low
            if bar["low"] == seg["low"].min():
                fractals.append({
                    "level": round(float(bar["low"]), 4),
                    "type": "fractal_low",
                    "date": str(bar["date"]),
                })

        # Cluster nearby levels
        fractals = self._cluster_fractals(fractals)
        return fractals

    def _cluster_fractals(self, fractals: list[dict]) -> list[dict]:
        """Merge fractals whose levels are within CLUSTER_PCT of each other."""
        if not fractals:
            return []

        sorted_f = sorted(fractals, key=lambda x: x["level"])
        clusters: list[list[dict]] = [[sorted_f[0]]]

        for f in sorted_f[1:]:
            if abs(f["level"] - clusters[-1][0]["level"]) / clusters[-1][0]["level"] <= self.CLUSTER_PCT:
                clusters[-1].append(f)
            else:
                clusters.append([f])

        result: list[dict] = []
        for group in clusters:
            avg_level = round(np.mean([g["level"] for g in group]), 4)
            types = set(g["type"] for g in group)
            level_type = "fractal_high" if "fractal_high" in types else "fractal_low"
            if "fractal_high" in types and "fractal_low" in types:
                level_type = "fractal_both"
            result.append({
                "level": avg_level,
                "type": level_type,
                "touches": len(group),
                "dates": [g["date"] for g in group],
            })

        return result

    # ------------------------------------------------------------------ #
    # MA levels as S/R
    # ------------------------------------------------------------------ #
    def _ma_levels(self, df: pd.DataFrame) -> list[dict]:
        levels: list[dict] = []
        for period in (20, 60, 120, 250):
            if len(df) < period:
                continue
            ma = df["close"].rolling(window=period, min_periods=1).mean().iloc[-1]
            if pd.notna(ma):
                levels.append({
                    "level": round(float(ma), 4),
                    "type": f"ma{period}",
                })
        return levels

    # ------------------------------------------------------------------ #
    # Round number levels
    # ------------------------------------------------------------------ #
    def _round_number_levels(self, price: float) -> list[dict]:
        levels: list[dict] = []

        # Determine granularity based on price magnitude
        if price < 5:
            step = 1
        elif price < 50:
            step = 5
        elif price < 200:
            step = 10
        elif price < 1000:
            step = 50
        else:
            step = 100

        lower = math.floor(price / step) * step
        upper = math.ceil(price / step) * step
        if lower == upper:
            upper += step

        # Include the two nearest rounds on each side.
        for offset in range(2):
            lv = lower - offset * step
            if lv > 0:
                levels.append({"level": float(lv), "type": "round_number"})
            uv = upper + offset * step
            levels.append({"level": float(uv), "type": "round_number"})

        # Deduplicate
        seen: set[float] = set()
        unique: list[dict] = []
        for lv in levels:
            if lv["level"] not in seen:
                seen.add(lv["level"])
                unique.append(lv)
        return unique

    # ------------------------------------------------------------------ #
    # Merge, label, and score all levels
    # ------------------------------------------------------------------ #
    def _merge_levels(
        self,
        pivots: dict,
        fractals: list[dict],
        ma_levels: list[dict],
        round_levels: list[dict],
        current_price: float,
    ) -> list[dict]:
        # Collect raw (level, source) pairs.
        raw: list[tuple[float, str]] = []

        for key in ("r1", "r2", "s1", "s2", "pp"):
            if key in pivots and pivots[key] is not None:
                raw.append((pivots[key], f"pivot_{key}"))

        for f in fractals:
            raw.append((f["level"], f["type"]))

        for m in ma_levels:
            raw.append((m["level"], m["type"]))

        for r in round_levels:
            raw.append((r["level"], r["type"]))

        if not raw:
            return []

        # Cluster all levels within CLUSTER_PCT
        raw.sort(key=lambda x: x[0])
        clusters: list[list[tuple[float, str]]] = [[raw[0]]]
        for lvl, src in raw[1:]:
            ref = np.mean([p[0] for p in clusters[-1]])
            if abs(lvl - ref) / max(ref, 0.01) <= self.CLUSTER_PCT:
                clusters[-1].append((lvl, src))
            else:
                clusters.append([(lvl, src)])

        result: list[dict] = []
        for group in clusters:
            avg_level = round(float(np.mean([p[0] for p in group])), 4)
            sources = list(set(p[1] for p in group))
            strength = len(sources)  # how many methods agree
            role = "support" if avg_level < current_price else "resistance"
            distance_pct = round((avg_level - current_price) / current_price * 100, 2)
            result.append({
                "level": avg_level,
                "role": role,
                "strength": strength,
                "sources": sources,
                "distance_pct": distance_pct,
            })

        result.sort(key=lambda x: x["level"])
        return result

    # ------------------------------------------------------------------ #
    @staticmethod
    def _empty_result() -> dict:
        return {
            "pivot_points": {},
            "fractal_levels": [],
            "ma_levels": [],
            "round_levels": [],
            "levels": [],
            "current_price": None,
        }
