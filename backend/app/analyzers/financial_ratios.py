"""
Pure computation module for fundamental financial ratios.

No I/O, no AI — takes raw financial DataFrames and computes metrics.
Supports both CN market (AkShare format) and US market (YFinance format).
"""

from dataclasses import dataclass, fields
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class FundamentalMetrics:
    pe: Optional[float] = None
    ps: Optional[float] = None
    pb: Optional[float] = None
    peg: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    revenue_growth_qoq: Optional[float] = None
    profit_growth_yoy: Optional[float] = None
    profit_growth_qoq: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    fcf_yield: Optional[float] = None
    market_cap: Optional[float] = None
    eps: Optional[float] = None
    book_value_per_share: Optional[float] = None
    dividend_yield: Optional[float] = None


def _safe_float(value) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        result = float(value)
        if np.isnan(result) or np.isinf(result):
            return None
        return result
    except (ValueError, TypeError):
        return None


def _safe_divide(numerator, denominator) -> Optional[float]:
    """Safely divide two numbers, returning None if impossible."""
    num = _safe_float(numerator)
    den = _safe_float(denominator)
    if num is None or den is None or den == 0:
        return None
    result = num / den
    if np.isnan(result) or np.isinf(result):
        return None
    return result


def _get_col(df: pd.DataFrame, candidates: list[str]):
    """
    Retrieve the first matching column from a DataFrame.

    For column-oriented DataFrames (AkShare CN), returns the latest
    non-null value from the matching column. For row-oriented DataFrames
    (YFinance US), returns the value from the most recent period column
    where the row index matches.
    """
    if df is None or df.empty:
        return None

    for col_name in candidates:
        # Column-oriented: the name is a column header
        if col_name in df.columns:
            series = df[col_name].dropna()
            if not series.empty:
                return _safe_float(series.iloc[0])

        # Row-oriented: the name is in the index
        if col_name in df.index:
            row = df.loc[col_name].dropna()
            if not row.empty:
                return _safe_float(row.iloc[0])

    return None


def _get_col_series(df: pd.DataFrame, candidates: list[str]) -> Optional[pd.Series]:
    """
    Retrieve a full Series for a column/row name across multiple periods.

    Returns the series with periods ordered most-recent-first.
    """
    if df is None or df.empty:
        return None

    for col_name in candidates:
        if col_name in df.columns:
            series = df[col_name].dropna()
            if not series.empty:
                return series

        if col_name in df.index:
            row = df.loc[col_name].dropna()
            if not row.empty:
                return row

    return None


def _compute_growth(series: Optional[pd.Series], periods_back: int = 1) -> Optional[float]:
    """
    Compute growth rate between the latest value and the value `periods_back` ago.

    The series is expected to be ordered most-recent-first.
    """
    if series is None or len(series) <= periods_back:
        return None
    current = _safe_float(series.iloc[0])
    previous = _safe_float(series.iloc[periods_back])
    if current is None or previous is None or previous == 0:
        return None
    growth = (current - previous) / abs(previous)
    if np.isnan(growth) or np.isinf(growth):
        return None
    return growth


class FundamentalCalculator:
    """
    Computes fundamental financial metrics from raw financial DataFrames.

    Supports:
      - CN market: AkShare-format DataFrames (column-oriented, Chinese headers)
      - US market: YFinance-format DataFrames (row-oriented, English headers)
    """

    # ------------------------------------------------------------------ #
    #  CN market column mappings (AkShare)
    # ------------------------------------------------------------------ #
    _CN_REVENUE = ["营业总收入", "营业收入"]
    _CN_NET_INCOME = ["净利润", "归属于母公司所有者的净利润"]
    _CN_OPERATING_INCOME = ["营业利润"]
    _CN_COST_OF_REVENUE = ["营业总成本", "营业成本"]
    _CN_TOTAL_ASSETS = ["总资产", "资产总计"]
    _CN_TOTAL_LIABILITIES = ["总负债", "负债合计"]
    _CN_EQUITY = ["股东权益合计", "归属于母公司所有者权益合计", "所有者权益合计"]
    _CN_CURRENT_ASSETS = ["流动资产合计"]
    _CN_CURRENT_LIABILITIES = ["流动负债合计"]
    _CN_OPERATING_CASHFLOW = ["经营活动产生的现金流量净额"]
    _CN_CAPEX = [
        "购建固定资产、无形资产和其他长期资产支付的现金",
        "购建固定资产无形资产和其他长期资产支付的现金",
        "资本性支出",
    ]

    # ------------------------------------------------------------------ #
    #  US market column mappings (YFinance)
    # ------------------------------------------------------------------ #
    _US_REVENUE = ["Total Revenue", "TotalRevenue", "totalRevenue"]
    _US_NET_INCOME = ["Net Income", "NetIncome", "netIncome", "Net Income From Continuing Operations"]
    _US_GROSS_PROFIT = ["Gross Profit", "GrossProfit", "grossProfit"]
    _US_OPERATING_INCOME = ["Operating Income", "OperatingIncome", "operatingIncome", "Ebit", "EBIT"]
    _US_TOTAL_ASSETS = ["Total Assets", "TotalAssets", "totalAssets"]
    _US_TOTAL_DEBT = ["Total Debt", "TotalDebt", "totalDebt", "Long Term Debt", "LongTermDebt"]
    _US_EQUITY = [
        "Total Stockholder Equity",
        "Stockholders Equity",
        "StockholdersEquity",
        "stockholdersEquity",
        "Total Stockholders Equity",
        "Ordinary Shares Number",
    ]
    _US_CURRENT_ASSETS = ["Total Current Assets", "TotalCurrentAssets", "totalCurrentAssets"]
    _US_CURRENT_LIABILITIES = [
        "Total Current Liabilities",
        "TotalCurrentLiabilities",
        "totalCurrentLiabilities",
    ]
    _US_OPERATING_CASHFLOW = [
        "Operating Cash Flow",
        "Total Cash From Operating Activities",
        "OperatingCashFlow",
        "operatingCashflow",
    ]
    _US_CAPEX = [
        "Capital Expenditures",
        "Capital Expenditure",
        "CapitalExpenditures",
        "capitalExpenditures",
    ]

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def compute(
        self,
        income_df: Optional[pd.DataFrame],
        balance_df: Optional[pd.DataFrame],
        cashflow_df: Optional[pd.DataFrame],
        quote_info: Optional[dict],
        market: str = "US",
    ) -> FundamentalMetrics:
        """
        Compute fundamental metrics from financial statements.

        Parameters
        ----------
        income_df : DataFrame or None
            Income statement data.
        balance_df : DataFrame or None
            Balance sheet data.
        cashflow_df : DataFrame or None
            Cash flow statement data.
        quote_info : dict or None
            Quote/info dict with keys like 'price', 'pe', 'pb', 'market_cap',
            'shares_outstanding', 'dividend_yield', etc.
        market : str
            'CN' for AkShare Chinese data, 'US' for YFinance data.

        Returns
        -------
        FundamentalMetrics
        """
        market = market.upper()
        qi = quote_info or {}

        if market == "CN":
            return self._compute_cn(income_df, balance_df, cashflow_df, qi)
        else:
            return self._compute_us(income_df, balance_df, cashflow_df, qi)

    def compute_peer_comparison(
        self,
        metrics: FundamentalMetrics,
        peer_metrics_list: list[FundamentalMetrics],
    ) -> dict[str, Optional[float]]:
        """
        Compute percentile ranking (0-100) for each metric relative to peers.

        Parameters
        ----------
        metrics : FundamentalMetrics
            The target stock's metrics.
        peer_metrics_list : list[FundamentalMetrics]
            Metrics for peer companies.

        Returns
        -------
        dict mapping metric name to percentile (0-100), or None if not computable.
        """
        if not peer_metrics_list:
            return {f.name: None for f in fields(FundamentalMetrics)}

        result: dict[str, Optional[float]] = {}

        for field in fields(FundamentalMetrics):
            name = field.name
            target_val = getattr(metrics, name)
            if target_val is None:
                result[name] = None
                continue

            peer_vals = [
                getattr(pm, name)
                for pm in peer_metrics_list
                if getattr(pm, name) is not None
            ]
            if not peer_vals:
                result[name] = None
                continue

            # Percentile: fraction of peers the target exceeds
            count_below = sum(1 for v in peer_vals if v < target_val)
            count_equal = sum(1 for v in peer_vals if v == target_val)
            total = len(peer_vals)

            # Use midpoint percentile: (count_below + 0.5 * count_equal) / total * 100
            percentile = (count_below + 0.5 * count_equal) / total * 100.0
            result[name] = round(percentile, 2)

        return result

    # ------------------------------------------------------------------ #
    #  CN market implementation
    # ------------------------------------------------------------------ #

    def _compute_cn(
        self,
        income_df: Optional[pd.DataFrame],
        balance_df: Optional[pd.DataFrame],
        cashflow_df: Optional[pd.DataFrame],
        qi: dict,
    ) -> FundamentalMetrics:
        # Check if income_df is actually THS financial abstract format
        if income_df is not None and not income_df.empty and "报告期" in income_df.columns:
            if "净资产收益率" in income_df.columns or "销售净利率" in income_df.columns:
                return self._compute_cn_ths(income_df, qi)

        m = FundamentalMetrics()

        # Extract latest values
        revenue = _get_col(income_df, self._CN_REVENUE)
        net_income = _get_col(income_df, self._CN_NET_INCOME)
        operating_income = _get_col(income_df, self._CN_OPERATING_INCOME)
        cost_of_revenue = _get_col(income_df, self._CN_COST_OF_REVENUE)

        total_assets = _get_col(balance_df, self._CN_TOTAL_ASSETS)
        total_liabilities = _get_col(balance_df, self._CN_TOTAL_LIABILITIES)
        equity = _get_col(balance_df, self._CN_EQUITY)
        current_assets = _get_col(balance_df, self._CN_CURRENT_ASSETS)
        current_liabilities = _get_col(balance_df, self._CN_CURRENT_LIABILITIES)

        operating_cf = _get_col(cashflow_df, self._CN_OPERATING_CASHFLOW)
        capex = _get_col(cashflow_df, self._CN_CAPEX)

        # ----- Valuation from quote_info ----- #
        m.pe = _safe_float(qi.get("pe")) or _safe_float(qi.get("pe_ttm"))
        m.pb = _safe_float(qi.get("pb"))
        m.market_cap = _safe_float(qi.get("market_cap")) or _safe_float(qi.get("total_mv"))
        m.dividend_yield = _safe_float(qi.get("dividend_yield"))

        price = _safe_float(qi.get("price")) or _safe_float(qi.get("current_price"))
        shares = _safe_float(qi.get("shares_outstanding")) or _safe_float(qi.get("total_shares"))

        # PS ratio
        if m.market_cap and revenue and revenue > 0:
            m.ps = m.market_cap / revenue
        elif price and shares and revenue and revenue > 0:
            m.ps = (price * shares) / revenue

        # EPS
        if net_income is not None and shares and shares > 0:
            m.eps = net_income / shares
        else:
            m.eps = _safe_float(qi.get("eps"))

        # Book value per share
        if equity is not None and shares and shares > 0:
            m.book_value_per_share = equity / shares

        # Fallback PE from price / eps
        if m.pe is None and price and m.eps and m.eps > 0:
            m.pe = price / m.eps

        # Fallback PB from price / bvps
        if m.pb is None and price and m.book_value_per_share and m.book_value_per_share > 0:
            m.pb = price / m.book_value_per_share

        # ----- Profitability ----- #
        m.roe = _safe_divide(net_income, equity)
        m.roa = _safe_divide(net_income, total_assets)

        if revenue and revenue > 0:
            if cost_of_revenue is not None:
                gross_profit = revenue - cost_of_revenue
                m.gross_margin = gross_profit / revenue
            m.net_margin = _safe_divide(net_income, revenue)
            m.operating_margin = _safe_divide(operating_income, revenue)

        # ----- Growth ----- #
        revenue_series = _get_col_series(income_df, self._CN_REVENUE)
        profit_series = _get_col_series(income_df, self._CN_NET_INCOME)

        m.revenue_growth_yoy = _compute_growth(revenue_series, periods_back=4)
        m.revenue_growth_qoq = _compute_growth(revenue_series, periods_back=1)
        m.profit_growth_yoy = _compute_growth(profit_series, periods_back=4)
        m.profit_growth_qoq = _compute_growth(profit_series, periods_back=1)

        # If YoY not available (fewer than 5 periods), try period-over-period as fallback
        if m.revenue_growth_yoy is None:
            m.revenue_growth_yoy = _compute_growth(revenue_series, periods_back=1)
        if m.profit_growth_yoy is None:
            m.profit_growth_yoy = _compute_growth(profit_series, periods_back=1)

        # PEG
        if m.pe is not None and m.profit_growth_yoy is not None and m.profit_growth_yoy > 0:
            growth_pct = m.profit_growth_yoy * 100
            if growth_pct > 0:
                m.peg = m.pe / growth_pct

        # ----- Financial Health ----- #
        if total_liabilities is not None and equity is not None and equity > 0:
            m.debt_to_equity = total_liabilities / equity
        m.current_ratio = _safe_divide(current_assets, current_liabilities)

        # FCF yield
        if operating_cf is not None and m.market_cap and m.market_cap > 0:
            capex_val = abs(capex) if capex is not None else 0
            fcf = operating_cf - capex_val
            m.fcf_yield = fcf / m.market_cap

        return m

    # ------------------------------------------------------------------ #
    #  CN THS financial abstract format
    # ------------------------------------------------------------------ #

    def _compute_cn_ths(self, df: pd.DataFrame, qi: dict) -> FundamentalMetrics:
        """Parse AkShare stock_financial_abstract_ths format (already has computed ratios)."""
        m = FundamentalMetrics()

        # Sort by report date desc to get latest first
        df = df.copy()
        df["报告期"] = pd.to_datetime(df["报告期"], errors="coerce")
        df = df.sort_values("报告期", ascending=False).reset_index(drop=True)

        def parse_pct(val) -> Optional[float]:
            """Parse '52.08%' or '6.25%' to float (e.g. 52.08)."""
            if val is None or val is False or (isinstance(val, float) and pd.isna(val)):
                return None
            s = str(val).replace("%", "").strip()
            try:
                return float(s)
            except (ValueError, TypeError):
                return None

        def parse_amount(val) -> Optional[float]:
            """Parse '646.27亿' or '1309.04亿' to float."""
            if val is None or val is False or (isinstance(val, float) and pd.isna(val)):
                return None
            s = str(val).strip()
            multiplier = 1.0
            if "万亿" in s:
                multiplier = 1e12
                s = s.replace("万亿", "")
            elif "亿" in s:
                multiplier = 1e8
                s = s.replace("亿", "")
            elif "万" in s:
                multiplier = 1e4
                s = s.replace("万", "")
            try:
                return float(s) * multiplier
            except (ValueError, TypeError):
                return None

        latest = df.iloc[0] if len(df) > 0 else {}
        prev = df.iloc[1] if len(df) > 1 else {}

        # Valuation from quote_info
        m.pe = _safe_float(qi.get("pe")) or _safe_float(qi.get("pe_ttm"))
        m.pb = _safe_float(qi.get("pb"))
        m.market_cap = _safe_float(qi.get("market_cap")) or _safe_float(qi.get("total_mv")) or _safe_float(qi.get("总市值"))
        m.dividend_yield = _safe_float(qi.get("dividend_yield"))

        # EPS, book value
        m.eps = _safe_float(latest.get("基本每股收益"))
        m.book_value_per_share = _safe_float(latest.get("每股净资产"))

        # Compute PE/PB from price if not in quote_info
        price = _safe_float(qi.get("price")) or _safe_float(qi.get("最新"))
        if m.pe is None and price and m.eps and m.eps > 0:
            m.pe = price / m.eps
        if m.pb is None and price and m.book_value_per_share and m.book_value_per_share > 0:
            m.pb = price / m.book_value_per_share

        # Profitability (already in %)
        m.roe = parse_pct(latest.get("净资产收益率"))
        m.net_margin = parse_pct(latest.get("销售净利率"))
        m.gross_margin = parse_pct(latest.get("销售毛利率"))

        # Growth rates
        m.revenue_growth_yoy = parse_pct(latest.get("营业总收入同比增长率"))
        m.profit_growth_yoy = parse_pct(latest.get("净利润同比增长率"))

        # Financial health
        asset_liability = parse_pct(latest.get("资产负债率"))
        if asset_liability is not None:
            # D/E ≈ asset_liability / (100 - asset_liability)
            if asset_liability < 100:
                m.debt_to_equity = asset_liability / (100 - asset_liability)
        property_ratio = _safe_float(latest.get("产权比率"))
        if m.debt_to_equity is None and property_ratio is not None:
            m.debt_to_equity = property_ratio

        m.current_ratio = _safe_float(latest.get("流动比率"))

        # Revenue for PS calculation
        revenue = parse_amount(latest.get("营业总收入"))
        if m.market_cap and revenue and revenue > 0:
            m.ps = m.market_cap / revenue

        # PEG
        if m.pe is not None and m.profit_growth_yoy is not None and m.profit_growth_yoy > 0:
            m.peg = m.pe / m.profit_growth_yoy

        # FCF yield from operating cashflow per share
        ocf_per_share = _safe_float(latest.get("每股经营现金流"))
        price = _safe_float(qi.get("price"))
        if ocf_per_share is not None and price and price > 0:
            m.fcf_yield = (ocf_per_share / price) * 100  # as percentage

        # ROA estimate: net_margin * revenue / total_assets
        # We have asset_liability, so total_assets ~ equity / (1 - asset_liability/100)
        if m.roe is not None and asset_liability is not None and asset_liability < 100:
            m.roa = m.roe * (1 - asset_liability / 100)

        return m

    # ------------------------------------------------------------------ #
    #  US market implementation
    # ------------------------------------------------------------------ #

    def _compute_us(
        self,
        income_df: Optional[pd.DataFrame],
        balance_df: Optional[pd.DataFrame],
        cashflow_df: Optional[pd.DataFrame],
        qi: dict,
    ) -> FundamentalMetrics:
        m = FundamentalMetrics()

        # Extract latest values
        revenue = _get_col(income_df, self._US_REVENUE)
        net_income = _get_col(income_df, self._US_NET_INCOME)
        gross_profit = _get_col(income_df, self._US_GROSS_PROFIT)
        operating_income = _get_col(income_df, self._US_OPERATING_INCOME)

        total_assets = _get_col(balance_df, self._US_TOTAL_ASSETS)
        total_debt = _get_col(balance_df, self._US_TOTAL_DEBT)
        equity = _get_col(balance_df, self._US_EQUITY)
        current_assets = _get_col(balance_df, self._US_CURRENT_ASSETS)
        current_liabilities = _get_col(balance_df, self._US_CURRENT_LIABILITIES)

        operating_cf = _get_col(cashflow_df, self._US_OPERATING_CASHFLOW)
        capex = _get_col(cashflow_df, self._US_CAPEX)

        # ----- Valuation from quote_info ----- #
        m.pe = _safe_float(qi.get("trailingPE")) or _safe_float(qi.get("pe")) or _safe_float(qi.get("forwardPE"))
        m.pb = _safe_float(qi.get("priceToBook")) or _safe_float(qi.get("pb"))
        m.market_cap = _safe_float(qi.get("marketCap")) or _safe_float(qi.get("market_cap"))
        m.dividend_yield = _safe_float(qi.get("dividendYield")) or _safe_float(qi.get("dividend_yield"))
        m.eps = _safe_float(qi.get("trailingEps")) or _safe_float(qi.get("eps"))

        price = (
            _safe_float(qi.get("currentPrice"))
            or _safe_float(qi.get("regularMarketPrice"))
            or _safe_float(qi.get("price"))
        )
        shares = (
            _safe_float(qi.get("sharesOutstanding"))
            or _safe_float(qi.get("shares_outstanding"))
        )

        # Market cap fallback
        if m.market_cap is None and price and shares:
            m.market_cap = price * shares

        # PS ratio
        m.ps = _safe_float(qi.get("priceToSalesTrailing12Months"))
        if m.ps is None and m.market_cap and revenue and revenue > 0:
            m.ps = m.market_cap / revenue

        # EPS fallback
        if m.eps is None and net_income is not None and shares and shares > 0:
            m.eps = net_income / shares

        # Book value per share
        m.book_value_per_share = _safe_float(qi.get("bookValue"))
        if m.book_value_per_share is None and equity is not None and shares and shares > 0:
            m.book_value_per_share = equity / shares

        # Fallback PE from price / eps
        if m.pe is None and price and m.eps and m.eps > 0:
            m.pe = price / m.eps

        # Fallback PB from price / bvps
        if m.pb is None and price and m.book_value_per_share and m.book_value_per_share > 0:
            m.pb = price / m.book_value_per_share

        # ----- Profitability ----- #
        m.roe = _safe_divide(net_income, equity)
        m.roa = _safe_divide(net_income, total_assets)

        if revenue and revenue > 0:
            if gross_profit is not None:
                m.gross_margin = gross_profit / revenue
            m.net_margin = _safe_divide(net_income, revenue)
            m.operating_margin = _safe_divide(operating_income, revenue)

        # ----- Growth ----- #
        revenue_series = _get_col_series(income_df, self._US_REVENUE)
        profit_series = _get_col_series(income_df, self._US_NET_INCOME)

        # YFinance typically provides annual data so periods_back=1 is YoY
        m.revenue_growth_yoy = _compute_growth(revenue_series, periods_back=1)
        m.profit_growth_yoy = _compute_growth(profit_series, periods_back=1)

        # QoQ: try periods_back=1 if quarterly data, otherwise attempt quarterly columns
        # For annual data this will be same as YoY; caller can provide quarterly DataFrames
        if revenue_series is not None and len(revenue_series) >= 3:
            m.revenue_growth_qoq = _compute_growth(revenue_series, periods_back=1)
        if profit_series is not None and len(profit_series) >= 3:
            m.profit_growth_qoq = _compute_growth(profit_series, periods_back=1)

        # PEG
        earnings_growth = _safe_float(qi.get("earningsGrowth")) or _safe_float(qi.get("earningsQuarterlyGrowth"))
        if m.pe is not None and earnings_growth is not None and earnings_growth > 0:
            m.peg = m.pe / (earnings_growth * 100)
        elif m.pe is not None and m.profit_growth_yoy is not None and m.profit_growth_yoy > 0:
            growth_pct = m.profit_growth_yoy * 100
            if growth_pct > 0:
                m.peg = m.pe / growth_pct

        # Also accept PEG directly from quote_info
        if m.peg is None:
            m.peg = _safe_float(qi.get("pegRatio"))

        # ----- Financial Health ----- #
        if total_debt is not None and equity is not None and equity > 0:
            m.debt_to_equity = total_debt / equity
        else:
            de_from_qi = _safe_float(qi.get("debtToEquity"))
            if de_from_qi is not None:
                # YFinance sometimes returns this as a percentage
                m.debt_to_equity = de_from_qi / 100.0 if de_from_qi > 10 else de_from_qi

        m.current_ratio = _safe_float(qi.get("currentRatio"))
        if m.current_ratio is None:
            m.current_ratio = _safe_divide(current_assets, current_liabilities)

        # FCF yield
        if operating_cf is not None and m.market_cap and m.market_cap > 0:
            capex_val = abs(capex) if capex is not None else 0
            fcf = operating_cf - capex_val
            m.fcf_yield = fcf / m.market_cap

        return m
