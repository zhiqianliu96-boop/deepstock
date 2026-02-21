"""Baostock-based CN daily data provider (fallback)."""
from __future__ import annotations

import asyncio
import logging

import pandas as pd

from app.services.data_providers.base import BaseCNDataProvider

logger = logging.getLogger(__name__)


class BaostockCNProvider(BaseCNDataProvider):
    """Fallback CN data provider using baostock (free, no API key)."""

    name = "baostock"
    priority = 2

    def is_available(self) -> bool:
        try:
            import baostock  # noqa: F401
            return True
        except ImportError:
            return False

    async def fetch_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        try:
            import baostock as bs
        except ImportError:
            return pd.DataFrame()

        # Baostock uses sh/sz prefix format: sh.600519
        prefix = "sh" if code.startswith(("6", "9")) else "sz"
        bs_code = f"{prefix}.{code}"

        # Convert YYYYMMDD to YYYY-MM-DD
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:]}"

        def _fetch():
            lg = bs.login()
            if lg.error_code != "0":
                logger.warning("Baostock login failed: %s", lg.error_msg)
                return pd.DataFrame()

            try:
                rs = bs.query_history_k_data_plus(
                    bs_code,
                    "date,open,high,low,close,volume,amount",
                    start_date=start_fmt,
                    end_date=end_fmt,
                    frequency="d",
                    adjustflag="2",  # qfq (前复权)
                )
                rows = []
                while rs.error_code == "0" and rs.next():
                    rows.append(rs.get_row_data())

                if not rows:
                    return pd.DataFrame()

                df = pd.DataFrame(rows, columns=rs.fields)
                df = df.rename(columns={"amount": "turnover"})
                for col in ["open", "high", "low", "close", "volume", "turnover"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                df["date"] = pd.to_datetime(df["date"])
                return df
            finally:
                bs.logout()

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        except Exception as e:
            logger.warning("Baostock CN daily fetch failed for %s: %s", code, e)
            return pd.DataFrame()
