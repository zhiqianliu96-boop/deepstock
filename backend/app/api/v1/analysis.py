import json
import math
import numpy as np
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.models.base import get_db

router = APIRouter()


class AnalysisRequest(BaseModel):
    code: str
    ai_provider: Optional[str] = None


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            v = float(obj)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super().default(obj)


@router.post("/analyze")
async def run_analysis(req: AnalysisRequest, db: Session = Depends(get_db)):
    from app.services.orchestrator import run_full_analysis

    result = await run_full_analysis(req.code, req.ai_provider, db)
    # Use custom encoder to handle numpy types
    content = json.loads(json.dumps(result, cls=NumpyEncoder, default=str))
    return JSONResponse(content=content)
