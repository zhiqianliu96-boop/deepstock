from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.stock import AnalysisRecord

router = APIRouter()


@router.get("")
def list_history(limit: int = 50, db: Session = Depends(get_db)):
    records = (
        db.query(AnalysisRecord)
        .order_by(AnalysisRecord.analysis_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "market": r.market,
            "analysis_date": r.analysis_date.isoformat() if r.analysis_date else None,
            "fundamental_score": r.fundamental_score,
            "technical_score": r.technical_score,
            "sentiment_score": r.sentiment_score,
            "composite_score": r.composite_score,
            "verdict": r.verdict,
            "ai_provider": r.ai_provider,
        }
        for r in records
    ]


@router.get("/{record_id}")
def get_history_detail(record_id: int, db: Session = Depends(get_db)):
    r = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not r:
        return {"error": "Not found"}
    return {
        "id": r.id,
        "code": r.code,
        "name": r.name,
        "market": r.market,
        "analysis_date": r.analysis_date.isoformat() if r.analysis_date else None,
        "fundamental_score": r.fundamental_score,
        "technical_score": r.technical_score,
        "sentiment_score": r.sentiment_score,
        "composite_score": r.composite_score,
        "verdict": r.verdict,
        "ai_provider": r.ai_provider,
        "fundamental_detail": r.fundamental_detail,
        "technical_detail": r.technical_detail,
        "sentiment_detail": r.sentiment_detail,
        "ai_synthesis": r.ai_synthesis,
    }
