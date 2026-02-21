from fastapi import APIRouter
from app.services.data_fetcher import fetch_stock_data, detect_market

router = APIRouter()


@router.get("/{code}/info")
async def get_stock_info(code: str):
    data = await fetch_stock_data(code, days=30)
    return {
        "code": data.code,
        "name": data.name,
        "market": data.market,
        "sector": data.sector,
        "industry": data.industry,
        "description": data.description,
        "quote": data.realtime_quote,
    }


@router.get("/{code}/daily")
async def get_daily_data(code: str, days: int = 365):
    data = await fetch_stock_data(code, days=days)
    if data.daily is not None and not data.daily.empty:
        records = data.daily.to_dict(orient="records")
        for r in records:
            for k, v in r.items():
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
        return {"code": code, "market": data.market, "data": records}
    return {"code": code, "market": data.market, "data": []}


@router.get("/{code}/financials")
async def get_financials(code: str):
    data = await fetch_stock_data(code, days=30)
    result = {}
    for name, df in [
        ("income_statement", data.income_statement),
        ("balance_sheet", data.balance_sheet),
        ("cash_flow", data.cash_flow),
    ]:
        if df is not None and not df.empty:
            records = df.head(8).to_dict(orient="records")
            for r in records:
                for k, v in r.items():
                    if hasattr(v, "isoformat"):
                        r[k] = v.isoformat()
                    elif isinstance(v, float) and (v != v):  # NaN check
                        r[k] = None
            result[name] = records
        else:
            result[name] = []
    return {"code": code, "market": data.market, **result}


@router.get("/{code}/intraday")
async def get_intraday_data(code: str, period: int = 5, adjust: str = "qfq"):
    """Get intraday (minute-level) K-line data.

    Args:
        code: Stock code
        period: Candle period in minutes (1, 5, 15, 30, 60)
        adjust: Price adjustment (qfq=forward, hfq=backward)
    """
    market = detect_market(code)

    try:
        if market == "CN":
            import akshare as ak
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=str(period), adjust=adjust)
            if df is not None and not df.empty:
                col_map = {
                    "时间": "time", "开盘": "open", "收盘": "close",
                    "最高": "high", "最低": "low", "成交量": "volume",
                    "成交额": "turnover", "涨跌幅": "pct_change",
                }
                df = df.rename(columns=col_map)
                records = df.to_dict(orient="records")
                return {"code": code, "market": market, "period": period, "data": records}

        elif market == "HK":
            try:
                import akshare as ak
                hk_code = code.replace(".HK", "").zfill(5)
                df = ak.stock_hk_hist_min_em(symbol=hk_code, period=str(period), adjust=adjust)
                if df is not None and not df.empty:
                    col_map = {
                        "时间": "time", "开盘": "open", "收盘": "close",
                        "最高": "high", "最低": "low", "成交量": "volume",
                    }
                    df = df.rename(columns=col_map)
                    records = df.to_dict(orient="records")
                    return {"code": code, "market": market, "period": period, "data": records}
            except Exception:
                pass
            # YFinance fallback for HK
            import yfinance as yf
            yf_code = f"{code.replace('.HK', '').zfill(5)}.HK"
            interval_map = {1: "1m", 5: "5m", 15: "15m", 30: "30m", 60: "60m"}
            interval = interval_map.get(period, "5m")
            ticker = yf.Ticker(yf_code)
            df = ticker.history(period="5d", interval=interval)
            if df is not None and not df.empty:
                df = df.reset_index()
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                if "datetime" in df.columns:
                    df["time"] = df["datetime"].astype(str)
                elif "date" in df.columns:
                    df["time"] = df["date"].astype(str)
                records = df.to_dict(orient="records")
                for r in records:
                    for k, v in r.items():
                        if hasattr(v, "isoformat"):
                            r[k] = v.isoformat()
                return {"code": code, "market": market, "period": period, "data": records}

        else:  # US
            import yfinance as yf
            interval_map = {1: "1m", 5: "5m", 15: "15m", 30: "30m", 60: "60m"}
            interval = interval_map.get(period, "5m")
            yf_period = "1d" if period <= 5 else "5d"
            ticker = yf.Ticker(code)
            df = ticker.history(period=yf_period, interval=interval)
            if df is not None and not df.empty:
                df = df.reset_index()
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                if "datetime" in df.columns:
                    df["time"] = df["datetime"].astype(str)
                elif "date" in df.columns:
                    df["time"] = df["date"].astype(str)
                records = df.to_dict(orient="records")
                for r in records:
                    for k, v in r.items():
                        if hasattr(v, "isoformat"):
                            r[k] = v.isoformat()
                return {"code": code, "market": market, "period": period, "data": records}

    except Exception as e:
        return {"code": code, "market": market, "period": period, "data": [], "error": str(e)}

    return {"code": code, "market": market, "period": period, "data": []}
