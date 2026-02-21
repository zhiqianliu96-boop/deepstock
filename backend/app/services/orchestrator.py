"""
Main analysis orchestrator — runs 3 pillars in parallel, composites, AI synthesis, persist.
"""
from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import asdict
from datetime import datetime

logger = logging.getLogger(__name__)

WEIGHT_FUNDAMENTAL = 0.35
WEIGHT_TECHNICAL = 0.35
WEIGHT_SENTIMENT = 0.30
DEFAULT_SCORE = 50.0


def _verdict_from_composite(score: float) -> str:
    if score > 80:
        return "strong_buy"
    elif score >= 65:
        return "buy"
    elif score >= 45:
        return "hold"
    elif score >= 30:
        return "sell"
    else:
        return "strong_sell"


def _safe_asdict(obj):
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    try:
        return asdict(obj)
    except (TypeError, AttributeError):
        if hasattr(obj, "__dict__"):
            return vars(obj)
        return {}


def _sanitize_for_json(obj):
    """Recursively replace NaN/Inf/numpy types with JSON-compatible equivalents."""
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(obj, np.ndarray):
        return _sanitize_for_json(obj.tolist())
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj


def _extract_total(result, default: float = DEFAULT_SCORE) -> float:
    if isinstance(result, dict):
        score = result.get("total", default)
    elif hasattr(result, "total"):
        score = result.total
    else:
        score = default
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return default
    return float(score)


async def run_full_analysis(code: str, ai_provider: str | None, db, *, lang: str | None = None) -> dict:
    from app.services.data_fetcher import fetch_stock_data
    from app.services.fundamental import FundamentalService
    from app.services.technical import TechnicalService
    from app.services.sentiment import SentimentService
    from app.services.ai_synthesis import AISynthesizer
    from app.models.stock import AnalysisRecord

    # 1. Fetch data
    logger.info("Starting full analysis for %s", code)
    stock_data = await fetch_stock_data(code)

    # 2. Run 3 pillars in parallel
    async def _run_fundamental():
        try:
            return await FundamentalService().analyze(stock_data)
        except Exception as e:
            logger.error("Fundamental analysis failed for %s: %s", code, e, exc_info=True)
            return None

    async def _run_technical():
        try:
            return await TechnicalService().analyze(stock_data)
        except Exception as e:
            logger.error("Technical analysis failed for %s: %s", code, e, exc_info=True)
            return None

    async def _run_sentiment():
        try:
            return await SentimentService().analyze(stock_data)
        except Exception as e:
            logger.error("Sentiment analysis failed for %s: %s", code, e, exc_info=True)
            return None

    fundamental_result, technical_result, sentiment_result = await asyncio.gather(
        _run_fundamental(), _run_technical(), _run_sentiment()
    )

    # 3. Compute composite
    f_score = _extract_total(fundamental_result)
    t_score = _extract_total(technical_result)
    s_score = _extract_total(sentiment_result)

    composite = f_score * WEIGHT_FUNDAMENTAL + t_score * WEIGHT_TECHNICAL + s_score * WEIGHT_SENTIMENT
    verdict = _verdict_from_composite(composite)

    logger.info("Scores for %s — F:%.1f T:%.1f S:%.1f Composite:%.1f (%s)",
                code, f_score, t_score, s_score, composite, verdict)

    # 4. AI Synthesis
    ai_synthesis = {}
    try:
        ai_synthesis = await AISynthesizer().synthesize(
            fundamental_score=fundamental_result,
            technical_score=technical_result,
            sentiment_score=sentiment_result,
            stock_data=stock_data,
            composite_score=composite,
            ai_provider_name=ai_provider,
            lang=lang,
        )
    except Exception as e:
        logger.error("AI synthesis failed for %s: %s", code, e, exc_info=True)
        ai_synthesis = {"summary": f"AI synthesis unavailable: {e}", "verdict": verdict}

    # Override verdict with AI if provided
    if ai_synthesis.get("verdict") and ai_synthesis["verdict"] in (
        "strong_buy", "buy", "hold", "sell", "strong_sell"
    ):
        verdict = ai_synthesis["verdict"]

    # 5. Convert to dicts
    f_detail = _sanitize_for_json(_safe_asdict(fundamental_result))
    t_detail = _sanitize_for_json(_safe_asdict(technical_result))
    s_detail = _sanitize_for_json(_safe_asdict(sentiment_result))
    ai_synthesis = _sanitize_for_json(ai_synthesis)

    # 6. Persist to DB (sync session)
    try:
        record = AnalysisRecord(
            code=code,
            name=stock_data.name,
            market=stock_data.market,
            fundamental_score=f_score,
            technical_score=t_score,
            sentiment_score=s_score,
            composite_score=composite,
            verdict=verdict,
            ai_provider=ai_provider or "gemini",
            fundamental_detail=f_detail,
            technical_detail=t_detail,
            sentiment_detail=s_detail,
            ai_synthesis=ai_synthesis,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info("Analysis saved for %s (id=%s)", code, record.id)
    except Exception as e:
        logger.error("Failed to save analysis for %s: %s", code, e, exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass

    # 7. Build response matching frontend types
    return _sanitize_for_json({
        "code": code,
        "name": stock_data.name,
        "market": stock_data.market,
        "sector": stock_data.sector,
        "industry": stock_data.industry,
        "fundamental_score": f_score,
        "technical_score": t_score,
        "sentiment_score": s_score,
        "composite_score": round(composite, 2),
        "verdict": verdict,
        "fundamental_detail": f_detail,
        "technical_detail": t_detail,
        "sentiment_detail": s_detail,
        "ai_synthesis": ai_synthesis,
        "chart_data": t_detail.get("chart_data"),
    })
