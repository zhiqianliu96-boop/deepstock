from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.models.base import get_db

router = APIRouter()


class AnalysisRequest(BaseModel):
    code: str
    ai_provider: Optional[str] = None


@router.post("/analyze")
async def run_analysis(req: AnalysisRequest, db: Session = Depends(get_db)):
    from app.services.orchestrator import run_full_analysis

    result = await run_full_analysis(req.code, req.ai_provider, db)
    return result
