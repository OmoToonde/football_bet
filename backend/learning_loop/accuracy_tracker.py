"""
Accuracy Tracker — Milestone 6
Computes model performance metrics from PredictionEvaluation rows.
Covers: overall accuracy, per-league, per-bet-type, confidence calibration, ROI.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.db.models import (
    Prediction, PredictionEvaluation, Match, League, PredictionMode,
)


async def get_overall_stats(db: AsyncSession) -> dict:
    """Return high-level model accuracy metrics."""
    evals = (await db.execute(
        select(PredictionEvaluation)
    )).scalars().all()

    if not evals:
        return _empty_stats("all")

    total      = len(evals)
    bet_evals  = [e for e in evals if e.bet_result in ("win", "loss")]
    won        = sum(1 for e in bet_evals if e.bet_result == "win")
    winner_ok  = sum(1 for e in evals if e.winner_correct)
    exact_ok   = sum(1 for e in evals if e.exact_score_correct)
    roi        = sum(e.profit_loss_result or 0 for e in bet_evals)

    return {
        "total_predictions": total,
        "bet_recommendations": len(bet_evals),
        "winner_accuracy": _pct(winner_ok, total),
        "bet_win_rate":     _pct(won, len(bet_evals)),
        "exact_score_accuracy": _pct(exact_ok, total),
        "avg_goal_margin_error": _avg(e.goal_margin_error for e in evals),
        "flat_stake_roi_units": round(roi, 2),
        "roi_per_bet_pct":  round(roi / max(1, len(bet_evals)) * 100, 1),
    }


async def get_stats_by_league(db: AsyncSession) -> list[dict]:
    """Return accuracy broken down by league."""
    rows = (await db.execute(
        select(PredictionEvaluation, Prediction, Match, League)
        .join(Prediction, PredictionEvaluation.prediction_id == Prediction.id)
        .join(Match, Prediction.match_id == Match.id)
        .join(League, Match.league_id == League.id)
    )).all()

    leagues: dict[str, list] = {}
    for ev, pred, match, league in rows:
        leagues.setdefault(league.name, []).append(ev)

    result = []
    for league_name, evals in sorted(leagues.items()):
        bet_evals = [e for e in evals if e.bet_result in ("win", "loss")]
        won       = sum(1 for e in bet_evals if e.bet_result == "win")
        winner_ok = sum(1 for e in evals if e.winner_correct)
        roi       = sum(e.profit_loss_result or 0 for e in bet_evals)

        result.append({
            "league": league_name,
            "total_predictions": len(evals),
            "winner_accuracy": _pct(winner_ok, len(evals)),
            "bet_win_rate":    _pct(won, len(bet_evals)),
            "roi_units":       round(roi, 2),
        })
    return result


async def get_stats_by_bet_type(db: AsyncSession) -> list[dict]:
    """Return accuracy broken down by recommended bet type."""
    rows = (await db.execute(
        select(PredictionEvaluation, Prediction)
        .join(Prediction, PredictionEvaluation.prediction_id == Prediction.id)
        .where(Prediction.mode == PredictionMode.PRE_MATCH)
    )).all()

    by_type: dict[str, list] = {}
    for ev, pred in rows:
        by_type.setdefault(pred.recommended_bet, []).append(ev)

    result = []
    for bet_type, evals in sorted(by_type.items()):
        bet_evals = [e for e in evals if e.bet_result in ("win", "loss")]
        won       = sum(1 for e in bet_evals if e.bet_result == "win")
        roi       = sum(e.profit_loss_result or 0 for e in bet_evals)

        result.append({
            "bet_type":        bet_type,
            "total":           len(evals),
            "bets_placed":     len(bet_evals),
            "win_rate":        _pct(won, len(bet_evals)),
            "roi_units":       round(roi, 2),
        })
    return result


async def get_confidence_calibration(db: AsyncSession) -> list[dict]:
    """
    Check whether stated confidence matches actual win rate.
    Well-calibrated: 60% confidence → ~60% actual wins.
    """
    rows = (await db.execute(
        select(PredictionEvaluation, Prediction)
        .join(Prediction, PredictionEvaluation.prediction_id == Prediction.id)
        .where(Prediction.confidence_score.isnot(None))
    )).all()

    BUCKETS = [(40, 50), (50, 60), (60, 70), (70, 80), (80, 95)]
    result = []
    for lo, hi in BUCKETS:
        bucket = [
            (ev, pred) for ev, pred in rows
            if pred.confidence_score is not None
            and lo <= pred.confidence_score < hi
        ]
        if not bucket:
            continue
        bet_evals = [(ev, pred) for ev, pred in bucket if ev.bet_result in ("win", "loss")]
        won = sum(1 for ev, _ in bet_evals if ev.bet_result == "win")

        result.append({
            "confidence_bracket": f"{lo}-{hi}%",
            "predictions": len(bucket),
            "stated_confidence_mid": (lo + hi) / 2,
            "actual_win_rate": _pct(won, len(bet_evals)),
            "calibration_gap": round(
                (lo + hi) / 2 - _pct(won, len(bet_evals)), 1
            ) if bet_evals else None,
        })
    return result


async def get_roi_summary(db: AsyncSession) -> dict:
    """Flat-staking ROI simulation summary."""
    rows = (await db.execute(
        select(PredictionEvaluation, Prediction)
        .join(Prediction, PredictionEvaluation.prediction_id == Prediction.id)
    )).all()

    total_bets  = sum(1 for ev, _ in rows if ev.bet_result in ("win", "loss"))
    total_wins  = sum(1 for ev, _ in rows if ev.bet_result == "win")
    total_voids = sum(1 for ev, _ in rows if ev.bet_result == "void")
    total_pl    = sum(ev.profit_loss_result or 0 for ev, _ in rows if ev.bet_result != "void")

    # Value bets only (value_rating >= 7)
    value_rows  = [(ev, p) for ev, p in rows if (p.value_rating or 0) >= 7]
    value_bets  = sum(1 for ev, _ in value_rows if ev.bet_result in ("win", "loss"))
    value_wins  = sum(1 for ev, _ in value_rows if ev.bet_result == "win")
    value_pl    = sum(ev.profit_loss_result or 0 for ev, _ in value_rows if ev.bet_result != "void")

    return {
        "all_bets": {
            "total": total_bets,
            "wins": total_wins,
            "voids": total_voids,
            "win_rate": _pct(total_wins, total_bets),
            "roi_units": round(total_pl, 2),
            "roi_pct": round(total_pl / max(1, total_bets) * 100, 1),
        },
        "value_bets_only": {
            "total": value_bets,
            "wins": value_wins,
            "win_rate": _pct(value_wins, value_bets),
            "roi_units": round(value_pl, 2),
            "roi_pct": round(value_pl / max(1, value_bets) * 100, 1),
        },
    }


def _pct(n: int, total: int) -> float:
    return round(n / total * 100, 1) if total else 0.0


def _avg(values) -> float:
    lst = list(values)
    lst = [v for v in lst if v is not None]
    return round(sum(lst) / len(lst), 2) if lst else 0.0


def _empty_stats(scope: str) -> dict:
    return {"scope": scope, "total_predictions": 0, "message": "No evaluations yet"}
