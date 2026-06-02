"""
Post-Match Evaluator — Milestone 6
Compares every prediction to the actual result and stores a PredictionEvaluation row.
Handles all bet types including Draw No Bet (void on draw) and Double Chance.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import (
    Match, Prediction, PredictionEvaluation, MatchStatus, PredictionMode,
)


def evaluate_bet_result(
    recommended_bet: str,
    home_score: int,
    away_score: int,
) -> str:
    """Return 'win', 'loss', or 'void' for a recommended bet given the actual scoreline."""
    bet = recommended_bet.lower()
    total = home_score + away_score
    home_won  = home_score > away_score
    away_won  = away_score > home_score
    drawn     = home_score == away_score

    if "no bet" in bet:
        return "void"

    # Draw No Bet markets
    if "draw no bet" in bet:
        if "home" in bet:
            if home_won:  return "win"
            if drawn:     return "void"
            return "loss"
        if "away" in bet:
            if away_won:  return "win"
            if drawn:     return "void"
            return "loss"

    # Double Chance
    if "double chance" in bet:
        if "home or draw" in bet:
            return "win" if home_won or drawn else "loss"
        if "away or draw" in bet:
            return "win" if away_won or drawn else "loss"
        if "home or away" in bet:
            return "win" if home_won or away_won else "loss"

    # Straight win / draw
    if "home win" in bet:
        return "win" if home_won else "loss"
    if "away win" in bet:
        return "win" if away_won else "loss"
    if "draw" in bet and "no bet" not in bet:
        return "win" if drawn else "loss"

    # Goals markets
    if "over 2.5" in bet:
        return "win" if total > 2 else "loss"
    if "under 2.5" in bet:
        return "win" if total < 3 else "loss"
    if "over 1.5" in bet:
        return "win" if total > 1 else "loss"
    if "under 1.5" in bet:
        return "win" if total < 2 else "loss"

    # Both teams to score
    if "both teams" in bet or "btts" in bet:
        return "win" if home_score > 0 and away_score > 0 else "loss"

    return "void"


def compute_profit_loss(bet_result: str, value_rating: float | None) -> float:
    """
    Flat-staking ROI simulation at 1 unit stake.
    Estimates decimal odds from value rating (rough proxy until real odds are stored).
    """
    if bet_result == "void":
        return 0.0

    # Rough implied odds from value rating
    # value_rating 1-3 = poor value (short odds ~1.5)
    # value_rating 6-7 = fair value (~2.0)
    # value_rating 8-9 = strong value (~2.5-3.0)
    if value_rating is None or value_rating < 1:
        estimated_odds = 1.80
    elif value_rating <= 3:
        estimated_odds = 1.60
    elif value_rating <= 5:
        estimated_odds = 1.90
    elif value_rating <= 7:
        estimated_odds = 2.10
    elif value_rating <= 9:
        estimated_odds = 2.60
    else:
        estimated_odds = 3.20

    if bet_result == "win":
        return round(estimated_odds - 1, 2)  # profit per unit staked
    return -1.0  # loss of 1 unit


async def evaluate_prediction(
    db: AsyncSession,
    prediction: Prediction,
    match: Match,
) -> PredictionEvaluation | None:
    """Evaluate one prediction against the actual result. Saves to DB."""
    if match.final_home_score is None or match.final_away_score is None:
        return None

    # Check if already evaluated
    existing = await db.execute(
        select(PredictionEvaluation)
        .where(PredictionEvaluation.prediction_id == prediction.id)
    )
    if existing.scalar_one_or_none():
        return None

    h = match.final_home_score
    a = match.final_away_score

    # Winner correct?
    predicted_home_win  = prediction.home_win_probability > prediction.away_win_probability
    predicted_draw      = prediction.draw_probability > max(
        prediction.home_win_probability, prediction.away_win_probability
    )
    actual_home_win = h > a
    actual_draw     = h == a

    winner_correct = (
        (predicted_home_win and actual_home_win) or
        (predicted_draw and actual_draw) or
        (not predicted_home_win and not predicted_draw and not actual_home_win and not actual_draw)
    )

    # Exact score
    predicted_score = prediction.expected_score or ""
    exact_correct = False
    if "-" in predicted_score:
        try:
            ph, pa = map(int, predicted_score.split("-"))
            exact_correct = (ph == h and pa == a)
        except ValueError:
            pass

    # Goal margin error (how far off was our total xG?)
    actual_total = h + a
    pred_total = (prediction.home_xg or 1.5) + (prediction.away_xg or 1.0)
    goal_margin_error = round(abs(pred_total - actual_total), 2)

    # Bet result + ROI
    bet_result = evaluate_bet_result(prediction.recommended_bet, h, a)
    profit_loss = compute_profit_loss(bet_result, prediction.value_rating)

    eval_row = PredictionEvaluation(
        prediction_id      = prediction.id,
        actual_home_score  = h,
        actual_away_score  = a,
        winner_correct     = winner_correct,
        exact_score_correct = exact_correct,
        goal_margin_error  = goal_margin_error,
        bet_result         = bet_result,
        profit_loss_result = profit_loss,
        evaluation_notes   = (
            f"Pred: {prediction.expected_score or '?'} | "
            f"Actual: {h}-{a} | "
            f"Bet: {prediction.recommended_bet} | "
            f"Result: {bet_result}"
        ),
    )
    db.add(eval_row)
    await db.commit()
    return eval_row


async def run_batch_evaluation(db: AsyncSession) -> dict:
    """Evaluate all unevaluated predictions for finished matches. Returns summary stats."""
    # Finished matches with predictions not yet evaluated
    matches_result = await db.execute(
        select(Match).where(Match.status == MatchStatus.FINISHED)
    )
    finished_matches = {m.id: m for m in matches_result.scalars().all()}

    preds_result = await db.execute(
        select(Prediction).where(
            Prediction.match_id.in_(list(finished_matches.keys())),
            Prediction.mode == PredictionMode.PRE_MATCH,
        )
    )
    predictions = preds_result.scalars().all()

    evaluated = 0
    skipped = 0
    for pred in predictions:
        match = finished_matches.get(pred.match_id)
        if not match:
            continue
        result = await evaluate_prediction(db, pred, match)
        if result:
            evaluated += 1
        else:
            skipped += 1

    return {"evaluated": evaluated, "skipped_already_done": skipped}
