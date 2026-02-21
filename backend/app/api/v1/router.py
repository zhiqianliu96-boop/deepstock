from fastapi import APIRouter
from app.api.v1 import analysis, stocks, history

api_router = APIRouter()
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
