"""
Volume analysis module.

Pure computation — takes a pandas DataFrame with daily OHLCV data and returns
volume-related metrics: volume ratio, divergences, unusual-volume days, and
volume trend classification.

Expected DataFrame columns: date, open, close, high, low, volume.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


class VolumeAnalyzer:
    """Analyze volume dynamics relative to price action."""

    def analyze(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return self._empty_result()

        df = df.copy()
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        volume_ratio = self._volume_ratio(df)
        divergences = self._volume_price_divergence(df)
        unusual_days = self._unusual_volume_days(df)
        volume_trend = self._volume_trend(df)

        return {
            "volume_ratio": volume_ratio,
            "divergences": divergences,
            "unusual_days": unusual_days,
            "volume_trend": volume_trend,
        }

    # ------------------------------------------------------------------ #
    # Volume ratio: today vs 5-day average
    # ------------------------------------------------------------------ #
    def _volume_ratio(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return {"ratio": None, "flag": "insufficient_data"}

        avg_5 = df["volume"].iloc[-6:-1].mean() if len(df) >= 6 else df["volume"].iloc[:-1].mean()
        if avg_5 == 0 or pd.isna(avg_5):
            return {"ratio": None, "flag": "no_volume"}

        ratio = float(df["volume"].iloc[-1] / avg_5)
        ratio = round(ratio, 4)

        if ratio > 2.0:
            flag = "unusual_high"
        elif ratio < 0.5:
            flag = "thin"
        else:
            flag = "normal"

        return {"ratio": ratio, "flag": flag}

    # ------------------------------------------------------------------ #
    # Volume-price divergence
    # ------------------------------------------------------------------ #
    def _volume_price_divergence(self, df: pd.DataFrame) -> list[dict]:
        divergences: list[dict] = []
        for window in (5, 10, 20):
            if len(df) < window + 1:
                continue

            recent = df.iloc[-window:]
            price_change = recent["close"].iloc[-1] - recent["close"].iloc[0]
            vol_slope = self._linear_slope(recent["volume"].values)

            if price_change > 0 and vol_slope < 0:
                divergences.append({
                    "window": window,
                    "type": "bearish_divergence",
                    "description": f"Price rising but volume declining over {window} days",
                })
            elif price_change < 0 and vol_slope < 0:
                divergences.append({
                    "window": window,
                    "type": "selling_exhaustion",
                    "description": f"Price falling with declining volume over {window} days — possible exhaustion",
                })
            elif price_change > 0 and vol_slope > 0:
                divergences.append({
                    "window": window,
                    "type": "confirmed_uptrend",
                    "description": f"Price and volume both rising over {window} days — healthy",
                })
            elif price_change < 0 and vol_slope > 0:
                divergences.append({
                    "window": window,
                    "type": "distribution",
                    "description": f"Price falling with rising volume over {window} days — distribution",
                })
        return divergences

    # ------------------------------------------------------------------ #
    # Unusual volume days (last 60 trading days)
    # ------------------------------------------------------------------ #
    def _unusual_volume_days(self, df: pd.DataFrame) -> list[dict]:
        lookback = min(len(df), 60)
        window = df.iloc[-lookback:].copy()
        window["vol_ma20"] = window["volume"].rolling(window=20, min_periods=1).mean()

        unusual: list[dict] = []
        for idx in range(len(window)):
            row = window.iloc[idx]
            if pd.isna(row["vol_ma20"]) or row["vol_ma20"] == 0:
                continue
            ratio = row["volume"] / row["vol_ma20"]
            if ratio > 2.0:
                price_chg = 0.0
                if idx > 0:
                    prev_close = window.iloc[idx - 1]["close"]
                    if prev_close != 0:
                        price_chg = round((row["close"] - prev_close) / prev_close * 100, 2)
                unusual.append({
                    "date": str(row["date"]),
                    "volume_ratio": round(float(ratio), 2),
                    "price_change_pct": price_chg,
                })
        return unusual

    # ------------------------------------------------------------------ #
    # Volume trend: 5-day avg vs 20-day avg
    # ------------------------------------------------------------------ #
    def _volume_trend(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return {"trend": "insufficient_data", "ratio_5_20": None}

        avg_5 = df["volume"].iloc[-5:].mean()
        avg_20 = df["volume"].iloc[-20:].mean()

        if avg_20 == 0 or pd.isna(avg_20):
            return {"trend": "no_volume", "ratio_5_20": None}

        ratio = float(avg_5 / avg_20)
        ratio = round(ratio, 4)

        if ratio > 1.3:
            trend = "expanding"
        elif ratio < 0.7:
            trend = "contracting"
        else:
            trend = "stable"

        return {"trend": trend, "ratio_5_20": ratio}

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _linear_slope(values: np.ndarray) -> float:
        """Return the linear regression slope of *values*."""
        n = len(values)
        if n < 2:
            return 0.0
        x = np.arange(n, dtype=float)
        y = values.astype(float)
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return 0.0
        x, y = x[mask], y[mask]
        slope = float(np.polyfit(x, y, 1)[0])
        return slope

    @staticmethod
    def _empty_result() -> dict:
        return {
            "volume_ratio": {"ratio": None, "flag": "no_data"},
            "divergences": [],
            "unusual_days": [],
            "volume_trend": {"trend": "no_data", "ratio_5_20": None},
        }
