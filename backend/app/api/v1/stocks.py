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
