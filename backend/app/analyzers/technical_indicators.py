"""
Technical indicators calculator.

Pure computation — takes a pandas DataFrame with daily OHLCV data and returns
a dict of indicator values, signals, and the enriched DataFrame.

Expected DataFrame columns: date, open, close, high, low, volume, turnover.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


class TechnicalIndicators:
    """Calculate standard technical indicators from a daily OHLCV DataFrame."""

    MA_PERIODS = [5, 10, 20, 60, 120, 250]

    # ------------------------------------------------------------------ #
    # public entry point
    # ------------------------------------------------------------------ #
    def compute(self, df: pd.DataFrame) -> dict:
        """Return a dict with all indicator values, signals, and the enriched DataFrame."""
        if df is None or df.empty:
            return self._empty_result()

        # Work on a copy so we never mutate the caller's data.
        df = df.copy()
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        ma_result = self._compute_ma(df)
        macd_result = self._compute_macd(df)
        rsi_result = self._compute_rsi(df)
        kdj_result = self._compute_kdj(df)
        boll_result = self._compute_bollinger(df)

        return {
            "ma": ma_result,
            "macd": macd_result,
            "rsi": rsi_result,
            "kdj": kdj_result,
            "bollinger": boll_result,
            "enriched_df": df,
        }

    # ------------------------------------------------------------------ #
    # Moving Averages
    # ------------------------------------------------------------------ #
    def _compute_ma(self, df: pd.DataFrame) -> dict:
        current_values: dict[str, float | None] = {}
        for p in self.MA_PERIODS:
            col = f"ma{p}"
            df[col] = df["close"].rolling(window=p, min_periods=1).mean()
            val = df[col].iloc[-1]
            current_values[col] = round(float(val), 4) if pd.notna(val) else None

        crossover_signals = self._detect_ma_crossovers(df)

        return {
            "current": current_values,
            "crossovers": crossover_signals,
        }

    def _detect_ma_crossovers(self, df: pd.DataFrame) -> list[dict]:
        """Check golden / death cross for MA5/MA20 and MA20/MA60."""
        signals: list[dict] = []
        pairs = [("ma5", "ma20"), ("ma20", "ma60")]
        for fast, slow in pairs:
            if fast not in df.columns or slow not in df.columns:
                continue
            if len(df) < 2:
                continue
            prev_fast = df[fast].iloc[-2]
            prev_slow = df[slow].iloc[-2]
            curr_fast = df[fast].iloc[-1]
            curr_slow = df[slow].iloc[-1]
            if pd.isna(prev_fast) or pd.isna(prev_slow) or pd.isna(curr_fast) or pd.isna(curr_slow):
                continue

            if prev_fast <= prev_slow and curr_fast > curr_slow:
                signals.append({
                    "type": "golden_cross",
                    "fast": fast,
                    "slow": slow,
                    "date": str(df["date"].iloc[-1]),
                })
            elif prev_fast >= prev_slow and curr_fast < curr_slow:
                signals.append({
                    "type": "death_cross",
                    "fast": fast,
                    "slow": slow,
                    "date": str(df["date"].iloc[-1]),
                })
        return signals

    # ------------------------------------------------------------------ #
    # MACD
    # ------------------------------------------------------------------ #
    def _compute_macd(self, df: pd.DataFrame) -> dict:
        try:
            import ta
            macd_obj = ta.trend.MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
            df["macd_dif"] = macd_obj.macd()
            df["macd_dea"] = macd_obj.macd_signal()
            df["macd_hist"] = macd_obj.macd_diff()
        except Exception:
            df["macd_dif"] = self._ema(df["close"], 12) - self._ema(df["close"], 26)
            df["macd_dea"] = self._ema(df["macd_dif"], 9)
            df["macd_hist"] = 2.0 * (df["macd_dif"] - df["macd_dea"])

        dif = self._last(df, "macd_dif")
        dea = self._last(df, "macd_dea")
        hist = self._last(df, "macd_hist")

        signal = self._macd_signal(df)

        return {
            "dif": dif,
            "dea": dea,
            "histogram": hist,
            "signal": signal,
        }

    def _macd_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 2:
            return "neutral"
        prev_dif = df["macd_dif"].iloc[-2]
        prev_dea = df["macd_dea"].iloc[-2]
        curr_dif = df["macd_dif"].iloc[-1]
        curr_dea = df["macd_dea"].iloc[-1]
        if pd.isna(prev_dif) or pd.isna(prev_dea) or pd.isna(curr_dif) or pd.isna(curr_dea):
            return "neutral"

        if prev_dif <= prev_dea and curr_dif > curr_dea:
            return "bullish_cross"
        if prev_dif >= prev_dea and curr_dif < curr_dea:
            return "bearish_cross"
        if curr_dif > 0 and curr_dea > 0:
            return "above_zero"
        if curr_dif < 0 and curr_dea < 0:
            return "below_zero"
        return "neutral"

    # ------------------------------------------------------------------ #
    # RSI
    # ------------------------------------------------------------------ #
    def _compute_rsi(self, df: pd.DataFrame) -> dict:
        try:
            import ta
            rsi_obj = ta.momentum.RSIIndicator(df["close"], window=14)
            df["rsi"] = rsi_obj.rsi()
        except Exception:
            delta = df["close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14, min_periods=1).mean()
            avg_loss = loss.rolling(window=14, min_periods=1).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

        value = self._last(df, "rsi")
        if value is None:
            zone = "unknown"
        elif value < 30:
            zone = "oversold"
        elif value > 70:
            zone = "overbought"
        else:
            zone = "neutral"

        return {"value": value, "zone": zone}

    # ------------------------------------------------------------------ #
    # KDJ
    # ------------------------------------------------------------------ #
    def _compute_kdj(self, df: pd.DataFrame) -> dict:
        try:
            import ta
            stoch = ta.momentum.StochasticOscillator(
                df["high"], df["low"], df["close"],
                window=9, smooth_window=3,
            )
            df["kdj_k"] = stoch.stoch()
            df["kdj_d"] = stoch.stoch_signal()
            df["kdj_j"] = 3.0 * df["kdj_k"] - 2.0 * df["kdj_d"]
        except Exception:
            low_min = df["low"].rolling(window=9, min_periods=1).min()
            high_max = df["high"].rolling(window=9, min_periods=1).max()
            rsv = (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan) * 100.0
            df["kdj_k"] = rsv.ewm(com=2, adjust=False).mean()
            df["kdj_d"] = df["kdj_k"].ewm(com=2, adjust=False).mean()
            df["kdj_j"] = 3.0 * df["kdj_k"] - 2.0 * df["kdj_d"]

        k = self._last(df, "kdj_k")
        d = self._last(df, "kdj_d")
        j = self._last(df, "kdj_j")

        signal = self._kdj_signal(df, j)

        return {"k": k, "d": d, "j": j, "signal": signal}

    def _kdj_signal(self, df: pd.DataFrame, j: float | None) -> str:
        if len(df) < 2:
            return "neutral"
        prev_k = df["kdj_k"].iloc[-2]
        prev_d = df["kdj_d"].iloc[-2]
        curr_k = df["kdj_k"].iloc[-1]
        curr_d = df["kdj_d"].iloc[-1]
        if pd.isna(prev_k) or pd.isna(prev_d) or pd.isna(curr_k) or pd.isna(curr_d):
            return "neutral"

        if prev_k <= prev_d and curr_k > curr_d:
            signal = "golden_cross"
        elif prev_k >= prev_d and curr_k < curr_d:
            signal = "death_cross"
        else:
            signal = "neutral"

        if j is not None:
            if j > 80:
                signal += "|overbought"
            elif j < 20:
                signal += "|oversold"

        return signal

    # ------------------------------------------------------------------ #
    # Bollinger Bands
    # ------------------------------------------------------------------ #
    def _compute_bollinger(self, df: pd.DataFrame) -> dict:
        try:
            import ta
            bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
            df["boll_upper"] = bb.bollinger_hband()
            df["boll_mid"] = bb.bollinger_mavg()
            df["boll_lower"] = bb.bollinger_lband()
            df["boll_pband"] = bb.bollinger_pband()  # %B
            df["boll_wband"] = bb.bollinger_wband()  # bandwidth
        except Exception:
            df["boll_mid"] = df["close"].rolling(window=20, min_periods=1).mean()
            rolling_std = df["close"].rolling(window=20, min_periods=1).std()
            df["boll_upper"] = df["boll_mid"] + 2.0 * rolling_std
            df["boll_lower"] = df["boll_mid"] - 2.0 * rolling_std
            band_range = df["boll_upper"] - df["boll_lower"]
            df["boll_pband"] = (df["close"] - df["boll_lower"]) / band_range.replace(0, np.nan)
            df["boll_wband"] = band_range / df["boll_mid"].replace(0, np.nan)

        return {
            "upper": self._last(df, "boll_upper"),
            "middle": self._last(df, "boll_mid"),
            "lower": self._last(df, "boll_lower"),
            "bandwidth": self._last(df, "boll_wband"),
            "percent_b": self._last(df, "boll_pband"),
        }

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def _last(df: pd.DataFrame, col: str) -> float | None:
        if col not in df.columns or df[col].empty:
            return None
        val = df[col].iloc[-1]
        return round(float(val), 4) if pd.notna(val) else None

    @staticmethod
    def _empty_result() -> dict:
        return {
            "ma": {"current": {}, "crossovers": []},
            "macd": {"dif": None, "dea": None, "histogram": None, "signal": "neutral"},
            "rsi": {"value": None, "zone": "unknown"},
            "kdj": {"k": None, "d": None, "j": None, "signal": "neutral"},
            "bollinger": {
                "upper": None, "middle": None, "lower": None,
                "bandwidth": None, "percent_b": None,
            },
            "enriched_df": pd.DataFrame(),
        }
