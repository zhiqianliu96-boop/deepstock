"""Tencent Finance real-time quote provider (free, no API key).

Used as a fallback when AkShare realtime fails.
API: http://qt.gtimg.cn/q=sh600519
"""
from __future__ import annotations

import asyncio
import logging
import urllib.request

logger = logging.getLogger(__name__)


def _safe_num(val: str) -> float | None:
    """Convert a string to float, returning None on failure."""
    try:
        v = float(val)
        return v if v != 0.0 else None
    except (ValueError, TypeError):
        return None


async def fetch_tencent_realtime(code: str) -> dict:
    """Fetch real-time quote from Tencent Finance.

    Args:
        code: 6-digit CN stock code (e.g. "600519").

    Returns:
        dict with keys: price, open, high, low, volume, turnover, pe, pb,
        market_cap, turnover_rate, 52w_high, 52w_low.
        Returns empty dict on failure.
    """
    prefix = "sh" if code.startswith(("6", "9")) else "sz"
    url = f"http://qt.gtimg.cn/q={prefix}{code}"

    def _fetch():
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.qq.com",
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode("gbk", errors="replace")

    try:
        raw = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    except Exception as e:
        logger.debug("Tencent realtime fetch failed for %s: %s", code, e)
        return {}

    # Parse the response: v_sh600519="1~贵州茅台~600519~1680.00~..."
    try:
        data_str = raw.split('"')[1] if '"' in raw else ""
        if not data_str:
            return {}
        fields = data_str.split("~")
        if len(fields) < 50:
            return {}

        result = {
            "price": _safe_num(fields[3]),
            "open": _safe_num(fields[5]),
            "high": _safe_num(fields[33]),
            "low": _safe_num(fields[34]),
            "volume": _safe_num(fields[36]),      # 成交量(手)
            "turnover": _safe_num(fields[37]),     # 成交额(万)
            "turnover_rate": _safe_num(fields[38]),
            "pe": _safe_num(fields[39]),
            "pb": _safe_num(fields[46]) if len(fields) > 46 else None,
            "market_cap": _safe_num(fields[45]) if len(fields) > 45 else None,
            "52w_high": _safe_num(fields[33]),     # Approximate with day high
            "52w_low": _safe_num(fields[34]),      # Approximate with day low
        }

        # Remove None values
        return {k: v for k, v in result.items() if v is not None}
    except Exception as e:
        logger.debug("Tencent realtime parse failed for %s: %s", code, e)
        return {}
