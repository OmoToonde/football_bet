"""
Weight Adjuster — Milestone 6
Analyses evaluation data and suggests small adjustments to prediction model weights.
Generates human-readable suggestions; does NOT auto-apply weights.
A human (or the admin dashboard) reviews and approves changes.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import Prediction, PredictionEvaluation, PredictionMode
from backend.config import settings


# Minimum evaluations required before suggesting weight changes
MIN_SAMPLE = 20

# Maximum adjustment per cycle (prevents over-correction)
MAX_STEP = 0.02


async def suggest_weight_adjustments(db: AsyncSession) -> dict:
    """
    Analyse recent prediction errors and return suggested weight adjustments.
    Returns current weights, suggested weights, and reasoning.
    """
    rows = (await db.execute(
        select(PredictionEvaluation, Prediction)
        .join(Prediction, PredictionEvaluation.prediction_id == Prediction.id)
        .where(Prediction.mode == PredictionMode.PRE_MATCH)
    )).all()

    if len(rows) < MIN_SAMPLE:
        return {
            "status": "insufficient_data",
            "message": f"Need at least {MIN_SAMPLE} evaluated predictions. Have {len(rows)}.",
            "current_weights": _current_weights(),
        }

    correct   = [(ev, p) for ev, p in rows if ev.winner_correct]
    incorrect = [(ev, p) for ev, p in rows if not ev.winner_correct]

    suggestions = []
    adjustments: dict[str, float] = {}

    # ── Signal 1: High xG mismatches in wrong predictions ────────────────
    high_xg_wrong = sum(
        1 for ev, p in incorrect
        if p.home_xg is not None and p.away_xg is not None
        and abs((p.home_xg or 0) - (p.away_xg or 0)) > 0.8
    )
    if high_xg_wrong > len(incorrect) * 0.4:
        adjustments["weight_xg"] = -MAX_STEP
        suggestions.append(
            f"xG weight reduced: high xG differences in {high_xg_wrong} wrong predictions "
            f"({high_xg_wrong/max(1,len(incorrect)):.0%} of errors)"
        )
    elif high_xg_wrong < len(incorrect) * 0.15:
        adjustments["weight_xg"] = +MAX_STEP * 0.5
        suggestions.append("xG weight slightly increased: xG mismatches are not a major error source")

    # ── Signal 2: Overconfidence in close matches ────────────────────────
    high_conf_wrong = sum(
        1 for ev, p in incorrect
        if (p.confidence_score or 0) >= 65
    )
    if high_conf_wrong > len(incorrect) * 0.35:
        adjustments["weight_home_away"] = -MAX_STEP * 0.5
        adjustments["weight_recent_form"] = -MAX_STEP * 0.5
        suggestions.append(
            f"Form/home-away weights slightly reduced: {high_conf_wrong} high-confidence wrong predictions"
        )

    # ── Signal 3: Fixture congestion signal ─────────────────────────────
    # If rest days appeared as a pattern in correct predictions, increase its weight
    correct_avg_conf  = _avg(p.confidence_score or 50 for _, p in correct)
    incorrect_avg_conf = _avg(p.confidence_score or 50 for _, p in incorrect)
    if correct_avg_conf - incorrect_avg_conf < 3:
        adjustments["weight_fixture_congestion"] = +MAX_STEP * 0.5
        suggestions.append(
            "Fixture congestion weight increased: confidence isn't separating correct from incorrect well"
        )

    # ── Signal 4: Value bets under-performing ───────────────────────────
    value_wrong = sum(
        1 for ev, p in incorrect
        if (p.value_rating or 0) >= 7
    )
    value_total = sum(1 for _, p in rows if (p.value_rating or 0) >= 7)
    if value_total > 5 and value_wrong / value_total > 0.60:
        adjustments["weight_odds_movement"] = +MAX_STEP
        suggestions.append(
            f"Odds movement weight increased: {value_wrong}/{value_total} value bets lost, "
            "market may know more than the model"
        )

    # Build suggested weights
    current = _current_weights()
    suggested = {}
    for key, current_val in current.items():
        delta = adjustments.get(key, 0)
        suggested[key] = round(max(0.01, min(0.35, current_val + delta)), 4)

    # Re-normalise to sum to 1
    total = sum(suggested.values())
    suggested = {k: round(v / total, 4) for k, v in suggested.items()}

    return {
        "status": "suggestions_ready",
        "total_evaluated": len(rows),
        "correct_predictions": len(correct),
        "overall_accuracy": round(len(correct) / len(rows) * 100, 1),
        "current_weights": current,
        "suggested_weights": suggested,
        "adjustments": adjustments,
        "reasoning": suggestions or ["No significant adjustments needed at this time"],
        "note": "These are suggestions only. Apply via admin dashboard after review.",
    }


def _current_weights() -> dict[str, float]:
    s = settings
    return {
        "weight_recent_form":       s.weight_recent_form,
        "weight_home_away":         s.weight_home_away,
        "weight_xg":                s.weight_xg,
        "weight_attacking":         s.weight_attacking,
        "weight_defensive":         s.weight_defensive,
        "weight_player_availability": s.weight_player_availability,
        "weight_fixture_congestion": s.weight_fixture_congestion,
        "weight_h2h":               s.weight_h2h,
        "weight_odds_movement":     s.weight_odds_movement,
    }


def _avg(values) -> float:
    lst = [v for v in values if v is not None]
    return sum(lst) / len(lst) if lst else 0.0
