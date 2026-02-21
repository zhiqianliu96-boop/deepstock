"""
Fundamental analysis service.

Orchestrates data fetching, metric computation, and scoring to produce
a comprehensive fundamental analysis score for a stock.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from app.analyzers.financial_ratios import FundamentalCalculator, FundamentalMetrics
from app.services.data_fetcher import StockData


@dataclass
class FundamentalScore:
    total: float = 0.0  # 0-100
    valuation_score: float = 0.0  # 0-25
    profitability_score: float = 0.0  # 0-25
    growth_score: float = 0.0  # 0-25
    health_score: float = 0.0  # 0-25
    breakdown: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    peer_comparison: dict = field(default_factory=dict)
    company_profile: dict = field(default_factory=dict)


class FundamentalService:
    """
    Orchestrates fundamental analysis: computes metrics, applies scoring
    rules, and returns a FundamentalScore.
    """

    def __init__(self):
        self._calculator = FundamentalCalculator()

    async def analyze(self, stock_data: StockData) -> FundamentalScore:
        """
        Perform fundamental analysis on a stock.

        Parameters
        ----------
        stock_data : StockData
            A StockData object containing financial DataFrames and metadata.
            Expected attributes:
                - income_statement (pd.DataFrame or None)
                - balance_sheet (pd.DataFrame or None)
                - cashflow (pd.DataFrame or None)
                - info (dict)
                - market (str): "CN" or "US"
                - peers (list[StockData], optional): peer stocks for comparison

        Returns
        -------
        FundamentalScore
        """
        info = getattr(stock_data, "info", {}) or {}
        market = getattr(stock_data, "market", "US") or "US"

        # Compute fundamental metrics
        metrics = self._calculator.compute(
            income_df=getattr(stock_data, "income_statement", None),
            balance_df=getattr(stock_data, "balance_sheet", None),
            cashflow_df=getattr(stock_data, "cashflow", None),
            quote_info=info,
            market=market,
        )

        # Compute peer comparison if peers are available
        peer_comparison: dict = {}
        peers = getattr(stock_data, "peers", None)
        if peers:
            peer_metrics_list = []
            for peer in peers:
                try:
                    peer_info = getattr(peer, "info", {}) or {}
                    peer_market = getattr(peer, "market", market) or market
                    pm = self._calculator.compute(
                        income_df=getattr(peer, "income_statement", None),
                        balance_df=getattr(peer, "balance_sheet", None),
                        cashflow_df=getattr(peer, "cashflow", None),
                        quote_info=peer_info,
                        market=peer_market,
                    )
                    peer_metrics_list.append(pm)
                except Exception:
                    continue
            if peer_metrics_list:
                peer_comparison = self._calculator.compute_peer_comparison(
                    metrics, peer_metrics_list
                )

        # Score each dimension
        valuation_score, valuation_breakdown = self._score_valuation(metrics)
        profitability_score, profitability_breakdown = self._score_profitability(metrics)
        growth_score, growth_breakdown = self._score_growth(metrics)
        health_score, health_breakdown = self._score_health(metrics)

        total = valuation_score + profitability_score + growth_score + health_score

        breakdown = {
            "valuation": valuation_breakdown,
            "profitability": profitability_breakdown,
            "growth": growth_breakdown,
            "health": health_breakdown,
        }

        company_profile = self._build_company_profile(info, market)

        # Convert metrics dataclass to dict, keeping None values for transparency
        metrics_dict = asdict(metrics)

        return FundamentalScore(
            total=round(total, 2),
            valuation_score=round(valuation_score, 2),
            profitability_score=round(profitability_score, 2),
            growth_score=round(growth_score, 2),
            health_score=round(health_score, 2),
            breakdown=breakdown,
            metrics=metrics_dict,
            peer_comparison=peer_comparison,
            company_profile=company_profile,
        )

    # ------------------------------------------------------------------ #
    #  Valuation scoring (0-25)
    # ------------------------------------------------------------------ #

    def _score_valuation(self, m: FundamentalMetrics) -> tuple[float, dict]:
        score = 0.0
        details: dict[str, Any] = {}

        # PE scoring (base 0-20)
        if m.pe is not None and m.pe > 0:
            if m.pe < 15:
                pe_score = 20.0
                details["pe"] = f"PE={m.pe:.1f} (<15): excellent value"
            elif m.pe <= 25:
                pe_score = 15.0
                details["pe"] = f"PE={m.pe:.1f} (15-25): fair value"
            elif m.pe <= 40:
                pe_score = 10.0
                details["pe"] = f"PE={m.pe:.1f} (25-40): moderately expensive"
            else:
                pe_score = 5.0
                details["pe"] = f"PE={m.pe:.1f} (>40): expensive"
            score += pe_score
        elif m.pe is not None and m.pe < 0:
            score += 3.0
            details["pe"] = f"PE={m.pe:.1f} (negative): company is unprofitable"
        else:
            details["pe"] = "PE data unavailable"

        # PEG bonus (up to +5)
        if m.peg is not None and m.peg > 0:
            if m.peg < 1.0:
                score += 5.0
                details["peg"] = f"PEG={m.peg:.2f} (<1): growth at reasonable price"
            elif m.peg < 1.5:
                score += 3.0
                details["peg"] = f"PEG={m.peg:.2f} (1-1.5): moderate growth valuation"
            elif m.peg < 2.0:
                score += 1.0
                details["peg"] = f"PEG={m.peg:.2f} (1.5-2): somewhat pricey for growth"
            else:
                details["peg"] = f"PEG={m.peg:.2f} (>2): expensive relative to growth"
        else:
            details["peg"] = "PEG data unavailable"

        # PB bonus (up to +3)
        if m.pb is not None and m.pb > 0:
            if m.pb < 1.0:
                score += 3.0
                details["pb"] = f"PB={m.pb:.2f} (<1): trading below book value"
            elif m.pb < 2.0:
                score += 1.5
                details["pb"] = f"PB={m.pb:.2f} (1-2): reasonable book valuation"
            else:
                details["pb"] = f"PB={m.pb:.2f} (>2): premium to book value"
        else:
            details["pb"] = "PB data unavailable"

        # PS bonus (up to +2)
        if m.ps is not None and m.ps > 0:
            if m.ps < 1.0:
                score += 2.0
                details["ps"] = f"PS={m.ps:.2f} (<1): very attractive price-to-sales"
            elif m.ps < 3.0:
                score += 1.0
                details["ps"] = f"PS={m.ps:.2f} (1-3): reasonable price-to-sales"
            else:
                details["ps"] = f"PS={m.ps:.2f} (>3): high price-to-sales"
        else:
            details["ps"] = "PS data unavailable"

        score = min(score, 25.0)
        return score, details

    # ------------------------------------------------------------------ #
    #  Profitability scoring (0-25)
    # ------------------------------------------------------------------ #

    def _score_profitability(self, m: FundamentalMetrics) -> tuple[float, dict]:
        score = 0.0
        details: dict[str, Any] = {}

        # ROE scoring (base 0-20)
        if m.roe is not None:
            roe_pct = m.roe * 100 if abs(m.roe) < 5 else m.roe  # handle already-percentage
            if roe_pct > 20:
                roe_score = 20.0
                details["roe"] = f"ROE={roe_pct:.1f}% (>20%): excellent return on equity"
            elif roe_pct > 15:
                roe_score = 15.0
                details["roe"] = f"ROE={roe_pct:.1f}% (15-20%): strong return on equity"
            elif roe_pct > 10:
                roe_score = 10.0
                details["roe"] = f"ROE={roe_pct:.1f}% (10-15%): adequate return on equity"
            elif roe_pct > 0:
                roe_score = 5.0
                details["roe"] = f"ROE={roe_pct:.1f}% (<10%): low return on equity"
            else:
                roe_score = 2.0
                details["roe"] = f"ROE={roe_pct:.1f}% (negative): destroying shareholder value"
            score += roe_score
        else:
            details["roe"] = "ROE data unavailable"

        # Net margin bonus (up to +5)
        if m.net_margin is not None:
            nm_pct = m.net_margin * 100 if abs(m.net_margin) < 5 else m.net_margin
            if nm_pct > 15:
                score += 5.0
                details["net_margin"] = f"Net margin={nm_pct:.1f}% (>15%): high profitability"
            elif nm_pct > 10:
                score += 3.0
                details["net_margin"] = f"Net margin={nm_pct:.1f}% (10-15%): good profitability"
            elif nm_pct > 5:
                score += 1.5
                details["net_margin"] = f"Net margin={nm_pct:.1f}% (5-10%): moderate profitability"
            elif nm_pct > 0:
                score += 0.5
                details["net_margin"] = f"Net margin={nm_pct:.1f}% (0-5%): thin margins"
            else:
                details["net_margin"] = f"Net margin={nm_pct:.1f}% (negative): unprofitable"
        else:
            details["net_margin"] = "Net margin data unavailable"

        # Gross margin bonus (up to +3)
        if m.gross_margin is not None:
            gm_pct = m.gross_margin * 100 if abs(m.gross_margin) < 5 else m.gross_margin
            if gm_pct > 50:
                score += 3.0
                details["gross_margin"] = f"Gross margin={gm_pct:.1f}% (>50%): strong pricing power"
            elif gm_pct > 30:
                score += 2.0
                details["gross_margin"] = f"Gross margin={gm_pct:.1f}% (30-50%): decent margins"
            elif gm_pct > 15:
                score += 1.0
                details["gross_margin"] = f"Gross margin={gm_pct:.1f}% (15-30%): competitive industry"
            else:
                details["gross_margin"] = f"Gross margin={gm_pct:.1f}% (<15%): low margin business"
        else:
            details["gross_margin"] = "Gross margin data unavailable"

        # ROA bonus (up to +2)
        if m.roa is not None:
            roa_pct = m.roa * 100 if abs(m.roa) < 5 else m.roa
            if roa_pct > 10:
                score += 2.0
                details["roa"] = f"ROA={roa_pct:.1f}% (>10%): efficient asset utilization"
            elif roa_pct > 5:
                score += 1.0
                details["roa"] = f"ROA={roa_pct:.1f}% (5-10%): adequate asset efficiency"
            else:
                details["roa"] = f"ROA={roa_pct:.1f}%: low asset efficiency"
        else:
            details["roa"] = "ROA data unavailable"

        score = min(score, 25.0)
        return score, details

    # ------------------------------------------------------------------ #
    #  Growth scoring (0-25)
    # ------------------------------------------------------------------ #

    def _score_growth(self, m: FundamentalMetrics) -> tuple[float, dict]:
        score = 0.0
        details: dict[str, Any] = {}

        # Revenue growth scoring (base 0-20)
        rev_growth = m.revenue_growth_yoy
        if rev_growth is not None:
            rg_pct = rev_growth * 100 if abs(rev_growth) < 5 else rev_growth
            if rg_pct > 20:
                rg_score = 20.0
                details["revenue_growth"] = f"Revenue growth={rg_pct:.1f}% (>20%): high growth"
            elif rg_pct > 10:
                rg_score = 15.0
                details["revenue_growth"] = f"Revenue growth={rg_pct:.1f}% (10-20%): solid growth"
            elif rg_pct > 0:
                rg_score = 10.0
                details["revenue_growth"] = f"Revenue growth={rg_pct:.1f}% (0-10%): modest growth"
            else:
                rg_score = 5.0
                details["revenue_growth"] = f"Revenue growth={rg_pct:.1f}% (<0%): declining revenue"
            score += rg_score
        else:
            details["revenue_growth"] = "Revenue growth data unavailable"

        # Profit growth consistency bonus (up to +5)
        profit_growth = m.profit_growth_yoy
        if profit_growth is not None:
            pg_pct = profit_growth * 100 if abs(profit_growth) < 5 else profit_growth
            if pg_pct > 20:
                score += 5.0
                details["profit_growth"] = f"Profit growth={pg_pct:.1f}% (>20%): strong earnings momentum"
            elif pg_pct > 10:
                score += 3.0
                details["profit_growth"] = f"Profit growth={pg_pct:.1f}% (10-20%): healthy earnings growth"
            elif pg_pct > 0:
                score += 1.5
                details["profit_growth"] = f"Profit growth={pg_pct:.1f}% (0-10%): modest earnings growth"
            else:
                details["profit_growth"] = f"Profit growth={pg_pct:.1f}% (<0%): declining earnings"
        else:
            details["profit_growth"] = "Profit growth data unavailable"

        # Acceleration bonus: QoQ growth exceeding YoY growth (up to +3)
        if (
            m.revenue_growth_qoq is not None
            and m.revenue_growth_yoy is not None
            and m.revenue_growth_qoq > m.revenue_growth_yoy
            and m.revenue_growth_qoq > 0
        ):
            score += 3.0
            details["acceleration"] = (
                f"Revenue accelerating: QoQ={m.revenue_growth_qoq * 100:.1f}% > "
                f"YoY={m.revenue_growth_yoy * 100:.1f}%"
            )
        elif m.revenue_growth_qoq is not None and m.revenue_growth_qoq > 0:
            score += 1.0
            details["acceleration"] = f"QoQ revenue growth={m.revenue_growth_qoq * 100:.1f}%: positive momentum"
        else:
            details["acceleration"] = "Acceleration data unavailable or negative"

        score = min(score, 25.0)
        return score, details

    # ------------------------------------------------------------------ #
    #  Financial health scoring (0-25)
    # ------------------------------------------------------------------ #

    def _score_health(self, m: FundamentalMetrics) -> tuple[float, dict]:
        score = 0.0
        details: dict[str, Any] = {}

        # Debt-to-equity scoring (base 0-20)
        if m.debt_to_equity is not None:
            de = m.debt_to_equity
            if de < 0.3:
                de_score = 20.0
                details["debt_to_equity"] = f"D/E={de:.2f} (<0.3): very low leverage"
            elif de < 0.5:
                de_score = 15.0
                details["debt_to_equity"] = f"D/E={de:.2f} (0.3-0.5): conservative leverage"
            elif de < 1.0:
                de_score = 10.0
                details["debt_to_equity"] = f"D/E={de:.2f} (0.5-1.0): moderate leverage"
            else:
                de_score = 5.0
                details["debt_to_equity"] = f"D/E={de:.2f} (>1.0): high leverage"
            score += de_score
        else:
            details["debt_to_equity"] = "Debt-to-equity data unavailable"

        # FCF bonus (+3 for positive)
        if m.fcf_yield is not None:
            if m.fcf_yield > 0:
                score += 3.0
                details["fcf"] = f"FCF yield={m.fcf_yield * 100:.1f}%: positive free cash flow"
            else:
                details["fcf"] = f"FCF yield={m.fcf_yield * 100:.1f}%: negative free cash flow"
        else:
            details["fcf"] = "FCF data unavailable"

        # Current ratio bonus (up to +3)
        if m.current_ratio is not None:
            if m.current_ratio > 2.0:
                score += 3.0
                details["current_ratio"] = (
                    f"Current ratio={m.current_ratio:.2f} (>2): strong short-term liquidity"
                )
            elif m.current_ratio >= 1.5:
                score += 2.0
                details["current_ratio"] = (
                    f"Current ratio={m.current_ratio:.2f} (1.5-2): adequate liquidity"
                )
            elif m.current_ratio >= 1.0:
                score += 1.0
                details["current_ratio"] = (
                    f"Current ratio={m.current_ratio:.2f} (1-1.5): tight liquidity"
                )
            else:
                details["current_ratio"] = (
                    f"Current ratio={m.current_ratio:.2f} (<1): liquidity risk"
                )
        else:
            details["current_ratio"] = "Current ratio data unavailable"

        # Dividend yield bonus (up to +2)
        if m.dividend_yield is not None and m.dividend_yield > 0:
            dy_pct = m.dividend_yield * 100 if m.dividend_yield < 1 else m.dividend_yield
            if dy_pct > 3:
                score += 2.0
                details["dividend"] = f"Dividend yield={dy_pct:.1f}%: attractive income"
            elif dy_pct > 1:
                score += 1.0
                details["dividend"] = f"Dividend yield={dy_pct:.1f}%: modest income"
            else:
                details["dividend"] = f"Dividend yield={dy_pct:.1f}%: minimal income"
        else:
            details["dividend"] = "No dividend or data unavailable"

        score = min(score, 25.0)
        return score, details

    # ------------------------------------------------------------------ #
    #  Company profile builder
    # ------------------------------------------------------------------ #

    def _build_company_profile(self, info: dict, market: str) -> dict:
        """Extract a clean company profile from the info dict."""
        profile: dict[str, Any] = {}

        # Common fields across markets
        key_mappings = {
            "name": ["shortName", "longName", "name", "股票简称"],
            "symbol": ["symbol", "ticker", "股票代码"],
            "sector": ["sector", "行业"],
            "industry": ["industry", "所属行业"],
            "exchange": ["exchange", "exchangeName", "市场"],
            "currency": ["currency", "financialCurrency"],
            "country": ["country", "国家"],
            "website": ["website"],
            "description": ["longBusinessSummary", "description", "公司简介"],
            "employees": ["fullTimeEmployees", "员工人数"],
            "market_cap": ["marketCap", "market_cap", "总市值"],
            "52_week_high": ["fiftyTwoWeekHigh", "52周最高"],
            "52_week_low": ["fiftyTwoWeekLow", "52周最低"],
        }

        for target_key, source_keys in key_mappings.items():
            for src in source_keys:
                val = info.get(src)
                if val is not None and val != "" and val != "N/A":
                    profile[target_key] = val
                    break

        profile["market"] = market
        return profile
