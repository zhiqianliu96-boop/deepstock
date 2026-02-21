"""Efinance-based CN daily data provider (fallback)."""
from __future__ import annotations

import asyncio
import logging

import pandas as pd

from app.services.data_providers.base import BaseCNDataProvider

logger = logging.getLogger(__name__)


class EfinanceCNProvider(BaseCNDataProvider):
    """Fallback CN data provider using efinance (free, no API key)."""

    name = "efinance"
    priority = 1

    def is_available(self) -> bool:
        try:
            import efinance  # noqa: F401
            return True
        except ImportError:
            return False

    async def fetch_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        try:
            import efinance as ef
        except ImportError:
            return pd.DataFrame()

        def _fetch():
            df = ef.stock.get_quote_history(code, beg=start, end=end)
            if df is None or df.empty:
                return pd.DataFrame()

            col_map = {
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
                "成交额": "turnover", "振幅": "amplitude",
                "涨跌幅": "pct_change", "涨跌额": "change",
                "换手率": "turnover_rate",
            }
            df = df.rename(columns=col_map)
            keep = [c for c in df.columns if c in col_map.values()]
            df = df[keep]
            df["date"] = pd.to_datetime(df["date"])
            return df

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        except Exception as e:
            logger.warning("Efinance CN daily fetch failed for %s: %s", code, e)
            return pd.DataFrame()
