"""
Institutional / fund-flow analysis (CN markets, AkShare data).

Pure computation — takes a pandas DataFrame returned by AkShare's fund-flow
interface and returns aggregated flow metrics.

Typical AkShare columns:
  日期, 主力净流入-净额, 超大单净流入-净额, 大单净流入-净额,
  中单净流入-净额, 小单净流入-净额
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# Column name mapping for AkShare fund flow data
_COL_MAP = {
    "日期": "date",
    "主力净流入-净额": "main_net",
    "超大单净流入-净额": "super_large_net",
    "大单净流入-净额": "large_net",
    "中单净流入-净额": "medium_net",
    "小单净流入-净额": "small_net",
}

_FLOW_COLS = ["main_net", "super_large_net", "large_net", "medium_net", "small_net"]


class InstitutionalFlowAnalyzer:
    """Analyze institutional fund flow data."""

    def analyze(self, fund_flow_df: pd.DataFrame | None) -> dict:
        if fund_flow_df is None or fund_flow_df.empty:
            return self._unavailable()

        df = self._normalize(fund_flow_df)
        if df.empty:
            return self._unavailable()

        main_force = self._main_force_flow(df)
        flow_trend = self._flow_trend(df)
        order_breakdown = self._order_breakdown(df)
        classification = self._classify(main_force, flow_trend)

        return {
            "main_force_flow": main_force,
            "flow_trend": flow_trend,
            "order_breakdown": order_breakdown,
            "classification": classification,
            "days_analyzed": len(df),
            "available": True,
        }

    # ------------------------------------------------------------------ #
    # normalize column names
    # ------------------------------------------------------------------ #
    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rename = {}
        for cn_name, en_name in _COL_MAP.items():
            if cn_name in df.columns:
                rename[cn_name] = en_name
        if rename:
            df.rename(columns=rename, inplace=True)

        # If "main_net" is still missing, we cannot proceed.
        if "main_net" not in df.columns:
            return pd.DataFrame()

        if "date" in df.columns:
            df.sort_values("date", inplace=True)
            df.reset_index(drop=True, inplace=True)

        # Ensure numeric
        for col in _FLOW_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df

    # ------------------------------------------------------------------ #
    # Main force net flow for recent windows
    # ------------------------------------------------------------------ #
    def _main_force_flow(self, df: pd.DataFrame) -> dict:
        result: dict = {}
        for window in (5, 10, 20):
            if len(df) >= window:
                total = float(df["main_net"].iloc[-window:].sum())
                avg = float(df["main_net"].iloc[-window:].mean())
            else:
                total = float(df["main_net"].sum())
                avg = float(df["main_net"].mean())
            result[f"sum_{window}d"] = round(total, 2)
            result[f"avg_{window}d"] = round(avg, 2)

        result["latest"] = round(float(df["main_net"].iloc[-1]), 2) if len(df) > 0 else 0.0
        return result

    # ------------------------------------------------------------------ #
    # Flow trend: accumulating / distributing / neutral
    # ------------------------------------------------------------------ #
    def _flow_trend(self, df: pd.DataFrame) -> dict:
        windows = {}
        for window in (5, 10, 20):
            if len(df) < window:
                continue
            recent = df["main_net"].iloc[-window:]
            positive_days = int((recent > 0).sum())
            negative_days = int((recent < 0).sum())
            ratio = positive_days / window

            if ratio >= 0.7:
                trend = "accumulating"
            elif ratio <= 0.3:
                trend = "distributing"
            else:
                trend = "neutral"

            windows[f"{window}d"] = {
                "trend": trend,
                "positive_days": positive_days,
                "negative_days": negative_days,
                "positive_ratio": round(ratio, 2),
            }
        return windows

    # ------------------------------------------------------------------ #
    # Order size breakdown (proportions)
    # ------------------------------------------------------------------ #
    def _order_breakdown(self, df: pd.DataFrame) -> dict:
        window = min(len(df), 20)
        recent = df.iloc[-window:]
        breakdown: dict = {}

        cols = ["super_large_net", "large_net", "medium_net", "small_net"]
        available_cols = [c for c in cols if c in recent.columns]
        if not available_cols:
            return breakdown

        totals = {c: float(recent[c].sum()) for c in available_cols}
        abs_total = sum(abs(v) for v in totals.values())
        if abs_total == 0:
            abs_total = 1.0  # prevent division by zero

        for col in available_cols:
            label = col.replace("_net", "")
            breakdown[label] = {
                "total": round(totals[col], 2),
                "proportion": round(abs(totals[col]) / abs_total * 100, 2),
                "direction": "inflow" if totals[col] > 0 else "outflow",
            }
        return breakdown

    # ------------------------------------------------------------------ #
    # Classification
    # ------------------------------------------------------------------ #
    def _classify(self, main_force: dict, flow_trend: dict) -> str:
        # Use the 10-day window as the primary signal, fall back to 5-day.
        for key in ("10d", "5d", "20d"):
            if key in flow_trend:
                return flow_trend[key]["trend"]
        # Fall back to sign of recent sum
        s = main_force.get("sum_5d", 0)
        if s > 0:
            return "accumulating"
        elif s < 0:
            return "distributing"
        return "neutral"

    # ------------------------------------------------------------------ #
    # Unavailable result
    # ------------------------------------------------------------------ #
    @staticmethod
    def _unavailable() -> dict:
        return {
            "main_force_flow": {},
            "flow_trend": {},
            "order_breakdown": {},
            "classification": "unavailable",
            "days_analyzed": 0,
            "available": False,
        }
