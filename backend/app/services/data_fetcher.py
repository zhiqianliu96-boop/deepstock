import re
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


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

    # Daily OHLCV
    try:
        df = ak.stock_zh_a_hist(
            symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq"
        )
        if df is not None and not df.empty:
            df.columns = ["date", "open", "close", "high", "low", "volume", "turnover",
                          "amplitude", "pct_change", "change", "turnover_rate"]
            df["date"] = pd.to_datetime(df["date"])
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

    # Income statement
    try:
        income = ak.stock_profit_sheet_by_report_em(symbol=code)
        if income is not None and not income.empty:
            data.income_statement = income
    except Exception as e:
        print(f"[CN] Income statement error for {code}: {e}")

    # Balance sheet
    try:
        balance = ak.stock_balance_sheet_by_report_em(symbol=code)
        if balance is not None and not balance.empty:
            data.balance_sheet = balance
    except Exception as e:
        print(f"[CN] Balance sheet error for {code}: {e}")

    # Cash flow
    try:
        cashflow = ak.stock_cash_flow_sheet_by_report_em(symbol=code)
        if cashflow is not None and not cashflow.empty:
            data.cash_flow = cashflow
    except Exception as e:
        print(f"[CN] Cash flow error for {code}: {e}")

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
        chip = ak.stock_cyq_em(symbol=code, adjust_date=datetime.now().strftime("%Y%m%d"))
        if chip is not None and not chip.empty:
            data.chip_data = chip
    except Exception as e:
        print(f"[CN] Chip data error for {code}: {e}")

    # Main business
    try:
        biz = ak.stock_zyjs_ths(symbol=code)
        if biz is not None and not biz.empty:
            data.main_business = biz
    except Exception as e:
        print(f"[CN] Main business error for {code}: {e}")

    # Realtime quote
    try:
        spot = ak.stock_zh_a_spot_em()
        if spot is not None and not spot.empty:
            row = spot[spot["代码"] == code]
            if not row.empty:
                row = row.iloc[0]
                data.realtime_quote = {
                    "price": row.get("最新价"),
                    "pe": row.get("市盈率-动态"),
                    "pb": row.get("市净率"),
                    "market_cap": row.get("总市值"),
                    "float_cap": row.get("流通市值"),
                    "volume": row.get("成交量"),
                    "turnover": row.get("成交额"),
                    "turnover_rate": row.get("换手率"),
                }
                if not data.name:
                    data.name = str(row.get("名称", ""))
    except Exception as e:
        print(f"[CN] Realtime quote error for {code}: {e}")

    # Sector peers
    try:
        if data.sector:
            peers = ak.stock_board_industry_cons_em(symbol=data.sector)
            if peers is not None and not peers.empty:
                data.sector_peers = peers
    except Exception as e:
        print(f"[CN] Sector peers error for {code}: {e}")

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
            df.columns = ["date", "open", "close", "high", "low", "volume", "turnover",
                          "amplitude", "pct_change", "change", "turnover_rate"]
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
