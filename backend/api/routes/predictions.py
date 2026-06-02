from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import Prediction, ScorelineProbability, FreshnessStatus

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
    return await _format_full(pred, db)


@router.post("/match/{match_id}/generate")
async def generate_match_prediction(match_id: int, db: AsyncSession = Depends(get_db)):
    """On-demand prediction generation for a specific match."""
    from backend.prediction_engine.predictor import generate_prediction
    pred = await generate_prediction(db, match_id)
    if not pred:
        raise HTTPException(
            status_code=422,
            detail="Prediction blocked: data is stale or match not found."
        )
    return await _format_full(pred, db)


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


async def _format_full(p: Prediction, db: AsyncSession) -> dict:
    """Include scoreline probabilities in the response."""
    base = _format(p)
    scorelines_result = await db.execute(
        select(ScorelineProbability)
        .where(ScorelineProbability.prediction_id == p.id)
        .order_by(ScorelineProbability.probability.desc())
    )
    base["scoreline_probabilities"] = [
        {
            "home_goals": s.home_goals,
            "away_goals": s.away_goals,
            "probability": s.probability,
        }
        for s in scorelines_result.scalars().all()
    ]
    return base
