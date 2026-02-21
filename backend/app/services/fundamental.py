"""
Fundamental analysis service.

Orchestrates data fetching, metric computation, and scoring to produce
a comprehensive fundamental analysis score for a stock.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import pandas as pd

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
        realtime = getattr(stock_data, "realtime_quote", {}) or {}
        quote_info = {**info, **realtime}
        market = getattr(stock_data, "market", "US") or "US"

        # Compute fundamental metrics
        metrics = self._calculator.compute(
            income_df=getattr(stock_data, "income_statement", None),
            balance_df=getattr(stock_data, "balance_sheet", None),
            cashflow_df=getattr(stock_data, "cash_flow", None),
            quote_info=quote_info,
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

        # --- Enrichment: surface new deep data without changing scores ---

        # DuPont decomposition
        dupont = self._compute_dupont(stock_data, metrics)
        if dupont:
            breakdown["dupont"] = dupont
            metrics_dict["dupont"] = dupont

        # Shareholder trend
        shareholders = self._compute_shareholder_trend(stock_data)
        if shareholders:
            breakdown["shareholders"] = shareholders
            metrics_dict["shareholders"] = shareholders

        # Analyst consensus
        analyst_consensus = self._compute_analyst_consensus(stock_data)
        if analyst_consensus:
            breakdown["analyst_consensus"] = analyst_consensus
            metrics_dict["analyst_consensus"] = analyst_consensus

        # Northbound flow signal (CN only)
        if market == "CN":
            nb_signal = self._compute_northbound_signal(stock_data)
            if nb_signal:
                breakdown["northbound_flow"] = nb_signal
                metrics_dict["northbound_flow"] = nb_signal

        # Margin sentiment (CN only)
        if market == "CN":
            margin_signal = self._compute_margin_sentiment(stock_data)
            if margin_signal:
                breakdown["margin_sentiment"] = margin_signal
                metrics_dict["margin_sentiment"] = margin_signal

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
    #  Enrichment helpers (no scoring changes — data surfacing only)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_dupont(stock_data: StockData, metrics: FundamentalMetrics) -> dict | None:
        """DuPont decomposition: ROE = net_margin × asset_turnover × equity_multiplier."""
        try:
            # Try from financial_indicators first
            fin_ind = getattr(stock_data, "financial_indicators", None)
            if fin_ind is not None and not fin_ind.empty:
                # AkShare financial_analysis_indicator has columns like 净资产收益率, 销售净利率, etc.
                latest = fin_ind.iloc[0]
                cols = fin_ind.columns.tolist()

                def _find_col(keywords):
                    for c in cols:
                        if all(k in str(c) for k in keywords):
                            try:
                                return float(latest[c])
                            except (ValueError, TypeError):
                                pass
                    return None

                roe_val = _find_col(["净资产收益率"]) or _find_col(["ROE"])
                net_margin_val = _find_col(["销售净利率"]) or _find_col(["净利率"])
                turnover_val = _find_col(["总资产周转率"]) or _find_col(["资产周转"])
                leverage_val = _find_col(["权益乘数"])

                if net_margin_val is not None and turnover_val is not None:
                    if leverage_val is None and roe_val and net_margin_val and turnover_val:
                        try:
                            leverage_val = roe_val / (net_margin_val * turnover_val / 100) if net_margin_val * turnover_val != 0 else None
                        except ZeroDivisionError:
                            leverage_val = None
                    return {
                        "net_margin": net_margin_val,
                        "asset_turnover": turnover_val,
                        "equity_multiplier": leverage_val,
                        "roe": roe_val,
                    }

            # Fallback: compute from metrics
            nm = metrics.net_margin
            roe = metrics.roe
            if nm is not None and roe is not None and nm != 0:
                nm_pct = nm * 100 if abs(nm) < 5 else nm
                roe_pct = roe * 100 if abs(roe) < 5 else roe
                # asset_turnover × equity_multiplier = ROE / net_margin
                combined = roe_pct / nm_pct if nm_pct != 0 else None
                return {
                    "net_margin": round(nm_pct, 2),
                    "asset_turnover_x_leverage": round(combined, 4) if combined else None,
                    "roe": round(roe_pct, 2),
                }
        except Exception:
            pass
        return None

    @staticmethod
    def _compute_shareholder_trend(stock_data: StockData) -> dict | None:
        """Extract top shareholder info and institutional ownership trend."""
        try:
            holders_df = getattr(stock_data, "top_shareholders", None)
            if holders_df is None or holders_df.empty:
                # US: try institutional_holders
                holders_df = getattr(stock_data, "institutional_holders", None)
                if holders_df is None or holders_df.empty:
                    return None

            result: dict[str, Any] = {}
            cols = holders_df.columns.tolist()

            # Try to extract top holders list
            holders_list = []
            for _, row in holders_df.head(10).iterrows():
                holder = {}
                for c in cols:
                    val = row[c]
                    if pd.notna(val):
                        if hasattr(val, "isoformat"):
                            holder[str(c)] = val.isoformat()
                        else:
                            holder[str(c)] = val
                holders_list.append(holder)

            result["top_holders"] = holders_list
            result["holder_count"] = len(holders_list)

            # Try to compute total institutional %
            pct_col = None
            for c in cols:
                if "比例" in str(c) or "%" in str(c) or "pct" in str(c).lower() or "shares" in str(c).lower():
                    pct_col = c
                    break
            if pct_col:
                try:
                    total_pct = holders_df.head(10)[pct_col].astype(float).sum()
                    result["top10_total_pct"] = round(float(total_pct), 2)
                except (ValueError, TypeError):
                    pass

            return result
        except Exception:
            return None

    @staticmethod
    def _compute_analyst_consensus(stock_data: StockData) -> dict | None:
        """Extract analyst ratings consensus."""
        try:
            ratings_df = getattr(stock_data, "analyst_ratings", None)
            if ratings_df is None or ratings_df.empty:
                return None

            result: dict[str, Any] = {}
            cols = [str(c) for c in ratings_df.columns.tolist()]

            # US: yfinance recommendations have columns like 'To Grade', 'Action'
            if any("grade" in c.lower() or "action" in c.lower() for c in cols):
                grade_col = next((c for c in cols if "grade" in c.lower()), None)
                if grade_col:
                    grades = ratings_df[grade_col].value_counts().to_dict()
                    buy_count = sum(v for k, v in grades.items() if any(w in str(k).lower() for w in ["buy", "overweight", "outperform"]))
                    hold_count = sum(v for k, v in grades.items() if any(w in str(k).lower() for w in ["hold", "neutral", "equal", "market perform"]))
                    sell_count = sum(v for k, v in grades.items() if any(w in str(k).lower() for w in ["sell", "underweight", "underperform"]))
                    result = {"buy": int(buy_count), "hold": int(hold_count), "sell": int(sell_count)}

            # CN: stock_comment_em has different column structure
            elif any("评级" in c or "目标" in c for c in cols):
                for c in cols:
                    if "评级" in c:
                        ratings = ratings_df[c].value_counts().to_dict()
                        result["ratings_distribution"] = {str(k): int(v) for k, v in ratings.items()}
                    if "目标价" in c or "目标" in c:
                        try:
                            targets = ratings_df[c].dropna().astype(float)
                            if not targets.empty:
                                result["target_price_mean"] = round(float(targets.mean()), 2)
                                result["target_price_high"] = round(float(targets.max()), 2)
                                result["target_price_low"] = round(float(targets.min()), 2)
                        except (ValueError, TypeError):
                            pass

            # Generic fallback: just report counts
            if not result:
                result["record_count"] = len(ratings_df)
                # Include latest few as raw data
                latest = []
                for _, row in ratings_df.head(5).iterrows():
                    entry = {}
                    for c in cols:
                        val = row[c]
                        if pd.notna(val):
                            if hasattr(val, "isoformat"):
                                entry[c] = val.isoformat()
                            else:
                                entry[c] = val
                    latest.append(entry)
                result["latest"] = latest

            return result
        except Exception:
            return None

    @staticmethod
    def _compute_northbound_signal(stock_data: StockData) -> dict | None:
        """Compute northbound (HSGT) flow trend for CN stocks."""
        try:
            nb_df = getattr(stock_data, "northbound_flow", None)
            if nb_df is None or nb_df.empty:
                return None

            result: dict[str, Any] = {}
            cols = [str(c) for c in nb_df.columns.tolist()]

            # Find net buy column
            net_col = None
            for c in cols:
                if "净买" in c or "净流入" in c or "net" in c.lower():
                    net_col = c
                    break

            if net_col:
                try:
                    recent = nb_df[net_col].head(20).astype(float)
                    result["recent_net_buy_total"] = round(float(recent.sum()), 2)
                    result["recent_5d_net"] = round(float(recent.head(5).sum()), 2)
                    result["recent_10d_net"] = round(float(recent.head(10).sum()), 2)
                    result["trend"] = "accumulating" if recent.head(5).sum() > 0 else "distributing"
                    # Daily values for charting
                    result["daily_net"] = [round(float(v), 2) for v in recent.tolist()]
                except (ValueError, TypeError):
                    pass

            # Find date column for labels
            date_col = None
            for c in cols:
                if "日期" in c or "date" in c.lower():
                    date_col = c
                    break
            if date_col:
                try:
                    result["dates"] = [str(d) for d in nb_df[date_col].head(20).tolist()]
                except Exception:
                    pass

            return result if result else None
        except Exception:
            return None

    @staticmethod
    def _compute_margin_sentiment(stock_data: StockData) -> dict | None:
        """Compute margin trading sentiment for CN stocks."""
        try:
            margin_df = getattr(stock_data, "margin_data", None)
            if margin_df is None or margin_df.empty:
                return None

            result: dict[str, Any] = {}
            cols = [str(c) for c in margin_df.columns.tolist()]

            # Find margin balance column
            balance_col = None
            for c in cols:
                if "融资余额" in c or "margin" in c.lower():
                    balance_col = c
                    break

            if balance_col:
                try:
                    balance = float(margin_df[balance_col].iloc[0])
                    result["margin_balance"] = balance
                except (ValueError, TypeError, IndexError):
                    pass

            # Find buy amount
            buy_col = None
            for c in cols:
                if "融资买入" in c:
                    buy_col = c
                    break
            if buy_col:
                try:
                    result["margin_buy"] = float(margin_df[buy_col].iloc[0])
                except (ValueError, TypeError, IndexError):
                    pass

            # Short selling balance
            short_col = None
            for c in cols:
                if "融券余额" in c:
                    short_col = c
                    break
            if short_col:
                try:
                    result["short_balance"] = float(margin_df[short_col].iloc[0])
                except (ValueError, TypeError, IndexError):
                    pass

            return result if result else None
        except Exception:
            return None

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
