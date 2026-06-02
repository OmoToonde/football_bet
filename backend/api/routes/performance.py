"""
Performance & Admin API — Milestone 6
Exposes model accuracy, calibration, ROI, and admin health endpoints.
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.learning_loop.evaluator import run_batch_evaluation
from backend.learning_loop.accuracy_tracker import (
    get_overall_stats,
    get_stats_by_league,
    get_stats_by_bet_type,
    get_confidence_calibration,
    get_roi_summary,
)
from backend.learning_loop.weight_adjuster import suggest_weight_adjustments

router = APIRouter(tags=["performance"])


# ── Model performance (public) ───────────────────────────────────────────────

@router.get("/performance/overview")
async def performance_overview(db: AsyncSession = Depends(get_db)):
    return await get_overall_stats(db)


@router.get("/performance/by-league")
async def performance_by_league(db: AsyncSession = Depends(get_db)):
    return {"leagues": await get_stats_by_league(db)}


@router.get("/performance/by-bet-type")
async def performance_by_bet_type(db: AsyncSession = Depends(get_db)):
    return {"bet_types": await get_stats_by_bet_type(db)}


@router.get("/performance/calibration")
async def performance_calibration(db: AsyncSession = Depends(get_db)):
    return {"calibration": await get_confidence_calibration(db)}


@router.get("/performance/roi")
async def performance_roi(db: AsyncSession = Depends(get_db)):
    return await get_roi_summary(db)


# ── Admin endpoints ──────────────────────────────────────────────────────────

@router.post("/admin/evaluate")
async def trigger_evaluation(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Run batch evaluation of all unevaluated predictions. Runs synchronously."""
    result = await run_batch_evaluation(db)
    return {"status": "done", **result}


@router.get("/admin/weight-suggestions")
async def weight_suggestions(db: AsyncSession = Depends(get_db)):
    return await suggest_weight_adjustments(db)


@router.get("/admin/data-health")
async def data_health(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from backend.db.models import Match, Prediction, PredictionEvaluation, MatchStatus

    total_matches    = (await db.execute(select(func.count()).select_from(Match))).scalar()
    finished         = (await db.execute(select(func.count()).where(Match.status == MatchStatus.FINISHED))).scalar()
    scheduled        = (await db.execute(select(func.count()).where(Match.status == MatchStatus.SCHEDULED))).scalar()
    live             = (await db.execute(select(func.count()).where(Match.status == MatchStatus.LIVE))).scalar()
    total_preds      = (await db.execute(select(func.count()).select_from(Prediction))).scalar()
    total_evals      = (await db.execute(select(func.count()).select_from(PredictionEvaluation))).scalar()
    unevaluated      = finished - total_evals

    return {
        "matches": {
            "total": total_matches,
            "finished": finished,
            "scheduled": scheduled,
            "live": live,
        },
        "predictions": {
            "total": total_preds,
            "evaluated": total_evals,
            "unevaluated_finished": max(0, unevaluated),
        },
    }
