import re
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


def _safe_num(val):
    """Convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


@dataclass
class StockData:
    code: str
    name: str = ""
    market: str = ""  # CN, US, HK
    sector: str = ""
    industry: str = ""
    description: str = ""
    daily: Optional[pd.DataFrame] = None  # OHLCV
    income_statement: Optional[pd.DataFrame] = None
    balance_sheet: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None
    info: dict = field(default_factory=dict)
    fund_flow: Optional[pd.DataFrame] = None  # CN only
    chip_data: Optional[pd.DataFrame] = None  # CN only
    main_business: Optional[pd.DataFrame] = None  # CN only
    realtime_quote: dict = field(default_factory=dict)
    sector_peers: Optional[pd.DataFrame] = None
    financial_indicators: Optional[pd.DataFrame] = None  # CN: ROE, margins, etc.
    top_shareholders: Optional[pd.DataFrame] = None  # CN: Top 10 shareholders
    industry_peers: Optional[pd.DataFrame] = None  # CN: Industry peer comparison
    analyst_ratings: Optional[pd.DataFrame] = None  # Analyst ratings/recommendations
    margin_data: Optional[pd.DataFrame] = None  # CN: Margin trading data
    block_trades: Optional[pd.DataFrame] = None  # CN: Block/bulk trades
    northbound_flow: Optional[pd.DataFrame] = None  # CN: HSGT northbound flow
    news_articles: Optional[pd.DataFrame] = None  # News from East Money
    institutional_holders: Optional[pd.DataFrame] = None  # US: Institutional holders
    options_data: dict = field(default_factory=dict)  # US: Options chain data


def detect_market(code: str) -> str:
    code = code.strip().upper()
    if re.match(r"^\d{6}$", code):
        return "CN"
    if re.match(r"^\d{5}$", code):
        return "HK"
    if re.match(r"^[A-Z]{1,5}$", code):
        return "US"
    if code.endswith(".HK"):
        return "HK"
    if code.endswith((".SH", ".SZ")):
        return "CN"
    return "US"


async def fetch_stock_data(code: str, days: int = 365) -> StockData:
    market = detect_market(code)
    if market == "CN":
        return await _fetch_cn(code, days)
    elif market == "HK":
        return await _fetch_hk(code, days)
    else:
        return await _fetch_us(code, days)


async def _fetch_cn(code: str, days: int) -> StockData:
    import akshare as ak

    data = StockData(code=code, market="CN")
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # Daily OHLCV — delegate to provider manager with failover
    try:
        from app.services.data_providers import CNDataProviderManager
        manager = CNDataProviderManager()
        df = await manager.fetch_daily(code, start, end)
        if df is not None and not df.empty:
            data.daily = df
    except Exception as e:
        print(f"[CN] Daily data error for {code}: {e}")

    # Company info
    try:
        info_df = ak.stock_individual_info_em(symbol=code)
        if info_df is not None and not info_df.empty:
            info_dict = dict(zip(info_df.iloc[:, 0], info_df.iloc[:, 1]))
            data.name = str(info_dict.get("股票简称", ""))
            data.sector = str(info_dict.get("行业", ""))
            data.industry = str(info_dict.get("行业", ""))
            data.info = info_dict
    except Exception as e:
        print(f"[CN] Info error for {code}: {e}")

    # Financial abstract (THS) — more reliable than individual statements
    try:
        fin_df = ak.stock_financial_abstract_ths(symbol=code)
        if fin_df is not None and not fin_df.empty:
            data.income_statement = fin_df  # Contains all key metrics
    except Exception as e:
        print(f"[CN] Financial abstract error for {code}: {e}")

    # Fallback: try individual statements
    if data.income_statement is None:
        for stmt_name, fetcher, attr in [
            ("Income", "stock_profit_sheet_by_report_em", "income_statement"),
            ("Balance", "stock_balance_sheet_by_report_em", "balance_sheet"),
            ("CashFlow", "stock_cash_flow_sheet_by_report_em", "cash_flow"),
        ]:
            try:
                df = getattr(ak, fetcher)(symbol=code)
                if df is not None and not df.empty:
                    setattr(data, attr, df)
            except Exception as e:
                print(f"[CN] {stmt_name} error for {code}: {e}")

    # Fund flow
    try:
        cn_market = "sh" if code.startswith(("6", "9")) else "sz"
        flow = ak.stock_individual_fund_flow(stock=code, market=cn_market)
        if flow is not None and not flow.empty:
            data.fund_flow = flow
    except Exception as e:
        print(f"[CN] Fund flow error for {code}: {e}")

    # Chip distribution
    try:
        chip = ak.stock_cyq_em(symbol=code)
        if chip is not None and not chip.empty:
            data.chip_data = chip
    except Exception as e:
        print(f"[CN] Chip data error for {code}: {e}")

    # Realtime quote — use bid_ask (fast single stock) + info we already have
    try:
        bid_df = ak.stock_bid_ask_em(symbol=code)
        if bid_df is not None and not bid_df.empty:
            bid_dict = dict(zip(bid_df.iloc[:, 0], bid_df.iloc[:, 1]))
            data.realtime_quote = {
                "price": _safe_num(bid_dict.get("最新")),
                "volume": _safe_num(bid_dict.get("总手")),
                "turnover": _safe_num(bid_dict.get("金额")),
                "turnover_rate": _safe_num(bid_dict.get("换手")),
                "high": _safe_num(bid_dict.get("最高")),
                "low": _safe_num(bid_dict.get("最低")),
            }
    except Exception:
        pass

    # Tencent Finance realtime fallback if AkShare realtime failed
    if not data.realtime_quote.get("price"):
        try:
            from app.services.data_providers.tencent_realtime import fetch_tencent_realtime
            tencent_quote = await fetch_tencent_realtime(code)
            if tencent_quote:
                # Merge Tencent data (don't overwrite existing non-None values)
                for k, v in tencent_quote.items():
                    if k not in data.realtime_quote or data.realtime_quote[k] is None:
                        data.realtime_quote[k] = v
        except Exception:
            pass

    # Merge PE/PB/market_cap from info (already fetched)
    if data.realtime_quote.get("price") is None and data.daily is not None and not data.daily.empty:
        data.realtime_quote["price"] = float(data.daily["close"].iloc[-1])
    # info dict may have these from stock_individual_info_em
    for cn_key, en_key in [("市盈率-动态", "pe"), ("市净率", "pb"), ("总市值", "market_cap"),
                            ("流通市值", "float_cap")]:
        if en_key not in data.realtime_quote or data.realtime_quote[en_key] is None:
            val = _safe_num(data.info.get(cn_key))
            if val is not None:
                data.realtime_quote[en_key] = val

    # Financial indicators (ROE, margin, etc.)
    try:
        fin_ind = ak.stock_financial_analysis_indicator(symbol=code)
        if fin_ind is not None and not fin_ind.empty:
            data.financial_indicators = fin_ind.head(20)
    except Exception as e:
        print(f"[CN] Financial indicators error for {code}: {e}")

    # Top 10 shareholders
    try:
        holders = ak.stock_gdfx_free_holding_detail_em(symbol=code)
        if holders is not None and not holders.empty:
            data.top_shareholders = holders.head(20)
    except Exception as e:
        print(f"[CN] Top shareholders error for {code}: {e}")

    # Industry peers comparison
    try:
        # First get the stock's industry board name from info
        industry_name = data.info.get("行业", "") or data.info.get("所属行业", "")
        if industry_name:
            peers = ak.stock_board_industry_cons_em(symbol=industry_name)
            if peers is not None and not peers.empty:
                data.industry_peers = peers.head(20)
    except Exception as e:
        print(f"[CN] Industry peers error for {code}: {e}")

    # Analyst ratings
    try:
        comments = ak.stock_comment_em(symbol=code)
        if comments is not None and not comments.empty:
            data.analyst_ratings = comments.head(30)
    except Exception as e:
        print(f"[CN] Analyst ratings error for {code}: {e}")

    # Margin trading data
    try:
        if code.startswith(("6", "9")):
            margin = ak.stock_margin_detail_sse(date=end)
        else:
            margin = ak.stock_margin_detail_szse(date=end)
        if margin is not None and not margin.empty:
            # Filter to this stock
            for col in margin.columns:
                if '代码' in col or 'code' in col.lower():
                    filtered = margin[margin[col].astype(str).str.contains(code)]
                    if not filtered.empty:
                        data.margin_data = filtered
                    break
    except Exception as e:
        print(f"[CN] Margin data error for {code}: {e}")

    # Block trades
    try:
        block = ak.stock_dzjy_mrtj(start_date=start, end_date=end)
        if block is not None and not block.empty:
            for col in block.columns:
                if '代码' in col or 'code' in col.lower():
                    filtered = block[block[col].astype(str).str.contains(code)]
                    if not filtered.empty:
                        data.block_trades = filtered.head(20)
                    break
    except Exception as e:
        print(f"[CN] Block trades error for {code}: {e}")

    # Northbound flow (HSGT)
    try:
        nb = ak.stock_hsgt_individual_em(symbol=code)
        if nb is not None and not nb.empty:
            data.northbound_flow = nb.head(60)
    except Exception as e:
        print(f"[CN] Northbound flow error for {code}: {e}")

    # East Money news
    try:
        news = ak.stock_news_em(symbol=code)
        if news is not None and not news.empty:
            data.news_articles = news.head(20)
    except Exception as e:
        print(f"[CN] News articles error for {code}: {e}")

    return data


async def _fetch_us(code: str, days: int) -> StockData:
    import yfinance as yf

    data = StockData(code=code, market="US")
    ticker = yf.Ticker(code)

    # Info
    try:
        info = ticker.info
        data.name = info.get("shortName", info.get("longName", code))
        data.sector = info.get("sector", "")
        data.industry = info.get("industry", "")
        data.description = info.get("longBusinessSummary", "")
        data.info = info
        data.realtime_quote = {
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb": info.get("priceToBook"),
            "ps": info.get("priceToSalesTrailing12Months"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        }
    except Exception as e:
        print(f"[US] Info error for {code}: {e}")

    # Daily OHLCV
    try:
        period = "2y" if days > 365 else "1y"
        df = ticker.history(period=period)
        if df is not None and not df.empty:
            df = df.reset_index()
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            data.daily = df
    except Exception as e:
        print(f"[US] Daily data error for {code}: {e}")

    # Financial statements
    try:
        fin = ticker.financials
        if fin is not None and not fin.empty:
            data.income_statement = fin.T.reset_index()
    except Exception as e:
        print(f"[US] Financials error for {code}: {e}")

    try:
        bs = ticker.balance_sheet
        if bs is not None and not bs.empty:
            data.balance_sheet = bs.T.reset_index()
    except Exception as e:
        print(f"[US] Balance sheet error for {code}: {e}")

    try:
        cf = ticker.cashflow
        if cf is not None and not cf.empty:
            data.cash_flow = cf.T.reset_index()
    except Exception as e:
        print(f"[US] Cash flow error for {code}: {e}")

    # Institutional holders
    try:
        inst = ticker.institutional_holders
        if inst is not None and not inst.empty:
            data.institutional_holders = inst
    except Exception as e:
        print(f"[US] Institutional holders error for {code}: {e}")

    # Analyst recommendations
    try:
        recs = ticker.recommendations
        if recs is not None and not recs.empty:
            data.analyst_ratings = recs.tail(20)
    except Exception as e:
        print(f"[US] Analyst recommendations error for {code}: {e}")

    # Options chain (for covered calls analysis)
    try:
        expiry_dates = ticker.options
        if expiry_dates and len(expiry_dates) > 0:
            # Get the nearest 2 expiry dates
            options_info = {"expiry_dates": list(expiry_dates[:4])}
            for exp in expiry_dates[:2]:
                try:
                    chain = ticker.option_chain(exp)
                    calls_df = chain.calls
                    puts_df = chain.puts
                    if calls_df is not None and not calls_df.empty:
                        options_info[f"calls_{exp}"] = calls_df.to_dict(orient="records")
                    if puts_df is not None and not puts_df.empty:
                        options_info[f"puts_{exp}"] = puts_df.to_dict(orient="records")
                except Exception:
                    pass
            data.options_data = options_info
    except Exception as e:
        print(f"[US] Options data error for {code}: {e}")

    return data


async def _fetch_hk(code: str, days: int) -> StockData:
    data = StockData(code=code, market="HK")

    hk_code = code.replace(".HK", "").zfill(5)

    # Try AkShare first for daily
    try:
        import akshare as ak

        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        df = ak.stock_hk_hist(
            symbol=hk_code, period="daily", start_date=start, end_date=end, adjust="qfq"
        )
        if df is not None and not df.empty:
            col_map = {
                "日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
                "最低": "low", "成交量": "volume", "成交额": "turnover",
                "振幅": "amplitude", "涨跌幅": "pct_change", "涨跌额": "change",
                "换手率": "turnover_rate",
            }
            df = df.rename(columns=col_map)
            df = df.drop(columns=[c for c in df.columns if c not in col_map.values()], errors="ignore")
            df["date"] = pd.to_datetime(df["date"])
            data.daily = df
    except Exception as e:
        print(f"[HK] AkShare daily error for {code}: {e}")

    # YFinance fallback for info + financials
    try:
        import yfinance as yf

        yf_code = f"{hk_code}.HK"
        ticker = yf.Ticker(yf_code)
        info = ticker.info
        data.name = info.get("shortName", info.get("longName", code))
        data.sector = info.get("sector", "")
        data.industry = info.get("industry", "")
        data.description = info.get("longBusinessSummary", "")
        data.info = info
        data.realtime_quote = {
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "pe": info.get("trailingPE"),
            "pb": info.get("priceToBook"),
            "market_cap": info.get("marketCap"),
        }

        if data.daily is None or data.daily.empty:
            df = ticker.history(period="1y")
            if df is not None and not df.empty:
                df = df.reset_index()
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
                data.daily = df

        fin = ticker.financials
        if fin is not None and not fin.empty:
            data.income_statement = fin.T.reset_index()

        bs = ticker.balance_sheet
        if bs is not None and not bs.empty:
            data.balance_sheet = bs.T.reset_index()

        cf = ticker.cashflow
        if cf is not None and not cf.empty:
            data.cash_flow = cf.T.reset_index()
    except Exception as e:
        print(f"[HK] YFinance fallback error for {code}: {e}")

    return data
