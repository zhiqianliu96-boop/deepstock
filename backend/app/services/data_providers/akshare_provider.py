"""AkShare-based CN daily data provider (primary)."""
from __future__ import annotations

import asyncio
import logging

import pandas as pd

from app.services.data_providers.base import BaseCNDataProvider

logger = logging.getLogger(__name__)

_CN_COL_MAP = {
    "日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
    "最低": "low", "成交量": "volume", "成交额": "turnover",
    "振幅": "amplitude", "涨跌幅": "pct_change", "涨跌额": "change",
    "换手率": "turnover_rate",
}


class AkShareCNProvider(BaseCNDataProvider):
    """Primary CN data provider using AkShare."""

    name = "akshare"
    priority = 0

    def is_available(self) -> bool:
        try:
            import akshare  # noqa: F401
            return True
        except ImportError:
            return False

    async def fetch_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        import akshare as ak

        def _fetch():
            df = ak.stock_zh_a_hist(
                symbol=code, period="daily",
                start_date=start, end_date=end, adjust="qfq",
            )
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns=_CN_COL_MAP)
            df = df.drop(
                columns=[c for c in df.columns if c not in _CN_COL_MAP.values()],
                errors="ignore",
            )
            df["date"] = pd.to_datetime(df["date"])
            return df

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        except Exception as e:
            logger.warning("AkShare CN daily fetch failed for %s: %s", code, e)
            return pd.DataFrame()
