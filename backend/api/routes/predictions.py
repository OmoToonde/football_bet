from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import Prediction, FreshnessStatus, RiskLevel

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/high-confidence")
async def get_high_confidence(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction)
        .where(Prediction.confidence_score >= 65)
        .where(Prediction.data_freshness_status == FreshnessStatus.FRESH)
        .order_by(Prediction.confidence_score.desc())
        .limit(10)
    )
    return {"predictions": [_format(p) for p in result.scalars().all()]}


@router.get("/value-bets")
async def get_value_bets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction)
        .where(Prediction.value_rating >= 7.0)
        .order_by(Prediction.value_rating.desc())
        .limit(10)
    )
    return {"predictions": [_format(p) for p in result.scalars().all()]}


@router.get("/match/{match_id}")
async def get_match_prediction(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction)
        .where(Prediction.match_id == match_id)
        .where(Prediction.mode == "pre_match")
        .order_by(Prediction.generated_at.desc())
    )
    pred = result.scalars().first()
    if not pred:
        raise HTTPException(status_code=404, detail="No prediction found for this match")
    return _format(pred)


def _format(p: Prediction) -> dict:
    return {
        "id": p.id,
        "match_id": p.match_id,
        "mode": p.mode.value,
        "recommended_bet": p.recommended_bet,
        "expected_score": p.expected_score,
        "home_win_probability": p.home_win_probability,
        "draw_probability": p.draw_probability,
        "away_win_probability": p.away_win_probability,
        "home_xg": p.home_xg,
        "away_xg": p.away_xg,
        "confidence_score": p.confidence_score,
        "risk_level": p.risk_level.value,
        "value_rating": p.value_rating,
        "explanation": p.explanation,
        "data_freshness_status": p.data_freshness_status.value,
        "lineups_confirmed": p.lineups_confirmed,
        "generated_at": p.generated_at.isoformat(),
    }
