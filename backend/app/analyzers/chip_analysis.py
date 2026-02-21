"""
Chip distribution analysis (CN markets, AkShare data from stock_cyq_em).

Pure computation — takes a pandas DataFrame with chip distribution data and
the current price, then returns a health assessment.

Typical AkShare columns: 获利比例, 平均成本, 集中度 (may vary).
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# AkShare column mapping
_COL_MAP = {
    "获利比例": "profit_ratio",
    "平均成本": "avg_cost",
    "集中度": "concentration",
    # Alternative column names
    "获利比例(%)": "profit_ratio",
    "平均成本(元)": "avg_cost",
    "集中度(%)": "concentration",
}


class ChipAnalyzer:
    """Analyze chip distribution data for CN stocks."""

    def analyze(
        self,
        chip_df: pd.DataFrame | None,
        current_price: float | None,
    ) -> dict:
        if chip_df is None or chip_df.empty:
            return self._unavailable("No chip data available")

        df = self._normalize(chip_df)
        if df.empty:
            return self._unavailable("Could not parse chip data columns")

        # Take the latest row (most recent data point).
        latest = df.iloc[-1]

        profit_ratio = self._safe_float(latest, "profit_ratio")
        avg_cost = self._safe_float(latest, "avg_cost")
        concentration = self._safe_float(latest, "concentration")

        health, assessment = self._assess(profit_ratio, avg_cost, concentration, current_price)

        return {
            "profit_ratio": profit_ratio,
            "avg_cost": avg_cost,
            "concentration": concentration,
            "current_price": current_price,
            "health": health,
            "assessment_text": assessment,
            "available": True,
        }

    # ------------------------------------------------------------------ #
    # internal
    # ------------------------------------------------------------------ #
    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rename = {}
        for cn, en in _COL_MAP.items():
            if cn in df.columns:
                rename[cn] = en
        if rename:
            df.rename(columns=rename, inplace=True)

        # Need at least profit_ratio or avg_cost to be useful
        if "profit_ratio" not in df.columns and "avg_cost" not in df.columns:
            return pd.DataFrame()

        for col in ("profit_ratio", "avg_cost", "concentration"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def _assess(
        self,
        profit_ratio: float | None,
        avg_cost: float | None,
        concentration: float | None,
        current_price: float | None,
    ) -> tuple[str, str]:
        """Return (health_label, assessment_text)."""
        parts: list[str] = []
        score = 0  # running score for health classification

        # --- profit ratio ---
        if profit_ratio is not None:
            if profit_ratio > 80:
                parts.append(
                    f"Profit ratio is high ({profit_ratio:.1f}%), indicating most holders "
                    "are in profit — strong holder confidence."
                )
                score += 2
            elif profit_ratio > 50:
                parts.append(
                    f"Profit ratio is moderate ({profit_ratio:.1f}%). Majority of holders "
                    "are profitable, but watch for resistance near cost peaks."
                )
                score += 1
            elif profit_ratio > 30:
                parts.append(
                    f"Profit ratio is below average ({profit_ratio:.1f}%). A significant "
                    "portion of holders are underwater — potential selling pressure."
                )
            else:
                parts.append(
                    f"Profit ratio is low ({profit_ratio:.1f}%). Most holders are "
                    "underwater — high risk of capitulation selling."
                )
                score -= 2

        # --- price vs avg cost ---
        if avg_cost is not None and current_price is not None:
            spread_pct = (current_price - avg_cost) / avg_cost * 100 if avg_cost != 0 else 0
            if current_price > avg_cost:
                parts.append(
                    f"Current price ({current_price:.2f}) is {spread_pct:.1f}% above "
                    f"average cost ({avg_cost:.2f}) — healthy."
                )
                score += 1
            else:
                parts.append(
                    f"Current price ({current_price:.2f}) is {abs(spread_pct):.1f}% below "
                    f"average cost ({avg_cost:.2f}) — underwater."
                )
                score -= 1

        # --- concentration ---
        if concentration is not None:
            if concentration < 10:
                parts.append(
                    f"Chip concentration is tight ({concentration:.1f}%) — chips are "
                    "highly concentrated, often bullish signal."
                )
                score += 1
            elif concentration < 20:
                parts.append(
                    f"Chip concentration is moderate ({concentration:.1f}%)."
                )
            else:
                parts.append(
                    f"Chip concentration is dispersed ({concentration:.1f}%) — chips are "
                    "spread out, may indicate weak consensus."
                )
                score -= 1

        # Determine health label
        if score >= 3:
            health = "strong"
        elif score >= 1:
            health = "healthy"
        elif score >= 0:
            health = "neutral"
        elif score >= -1:
            health = "weak"
        else:
            health = "unhealthy"

        assessment = " ".join(parts) if parts else "Insufficient chip data for assessment."
        return health, assessment

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _safe_float(row: pd.Series, col: str) -> float | None:
        if col not in row.index:
            return None
        val = row[col]
        if pd.isna(val):
            return None
        return round(float(val), 4)

    @staticmethod
    def _unavailable(reason: str = "") -> dict:
        return {
            "profit_ratio": None,
            "avg_cost": None,
            "concentration": None,
            "current_price": None,
            "health": "unavailable",
            "assessment_text": reason or "Chip data unavailable.",
            "available": False,
        }
