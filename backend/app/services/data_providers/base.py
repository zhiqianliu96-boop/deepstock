"""Abstract base class for CN market data providers."""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseCNDataProvider(ABC):
    """Abstract base for Chinese market daily OHLCV data providers."""

    name: str = "base"
    priority: int = 99

    @abstractmethod
    async def fetch_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        """Fetch daily OHLCV data for a CN stock.

        Args:
            code: 6-digit stock code (e.g. "600519").
            start: Start date in YYYYMMDD format.
            end: End date in YYYYMMDD format.

        Returns:
            DataFrame with columns: date, open, close, high, low, volume,
            and optionally: turnover, amplitude, pct_change, change, turnover_rate.
            Returns empty DataFrame on failure.
        """
        ...

    def is_available(self) -> bool:
        """Check if this provider's dependencies are installed."""
        return True
