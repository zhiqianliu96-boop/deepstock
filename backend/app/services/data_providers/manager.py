"""CN data provider manager with failover and optional retry."""
from __future__ import annotations

import logging

import pandas as pd

from app.services.data_providers.base import BaseCNDataProvider

logger = logging.getLogger(__name__)


class CNDataProviderManager:
    """Manages multiple CN data providers with priority-based failover.

    Tries providers in priority order (lowest number first).
    Falls back to the next provider if one fails or returns empty data.
    """

    def __init__(self):
        self._providers: list[BaseCNDataProvider] = []
        self._init_providers()

    def _init_providers(self):
        """Initialize providers in priority order, skipping unavailable ones."""
        # AkShare (priority 0) — always attempted first
        from app.services.data_providers.akshare_provider import AkShareCNProvider
        self._providers.append(AkShareCNProvider())

        # Efinance (priority 1) — optional
        try:
            from app.services.data_providers.efinance_provider import EfinanceCNProvider
            provider = EfinanceCNProvider()
            if provider.is_available():
                self._providers.append(provider)
                logger.info("Efinance CN provider available as fallback")
        except Exception:
            pass

        # Baostock (priority 2) — optional
        try:
            from app.services.data_providers.baostock_provider import BaostockCNProvider
            provider = BaostockCNProvider()
            if provider.is_available():
                self._providers.append(provider)
                logger.info("Baostock CN provider available as fallback")
        except Exception:
            pass

        self._providers.sort(key=lambda p: p.priority)
        available = [p.name for p in self._providers]
        logger.info("CNDataProviderManager initialized — providers: %s", available)

    async def fetch_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        """Fetch daily OHLCV using the first successful provider.

        Args:
            code: 6-digit stock code.
            start: Start date YYYYMMDD.
            end: End date YYYYMMDD.

        Returns:
            DataFrame with OHLCV data, or empty DataFrame if all fail.
        """
        for provider in self._providers:
            try:
                df = await provider.fetch_daily(code, start, end)
                if df is not None and not df.empty:
                    logger.debug(
                        "CN daily data from '%s': %d rows for %s",
                        provider.name, len(df), code,
                    )
                    return df
            except Exception:
                logger.warning(
                    "CN provider '%s' failed for %s",
                    provider.name, code, exc_info=True,
                )
                continue

        logger.error("All CN data providers failed for %s", code)
        return pd.DataFrame()
