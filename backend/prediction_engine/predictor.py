"""
Prediction Orchestrator
Runs the full pipeline for one match:
  feature_builder → outcome_model → score_model → value_engine
  → confidence_engine → risk_engine → explanation_engine → Prediction row
"""
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import (
    Match, Team, League, Prediction, ScorelineProbability,
    MatchDataSnapshot, FreshnessStatus, RiskLevel, PredictionMode,
)
from backend.data_pipeline.feature_store.feature_builder import (
    build_team_metrics, build_xg_estimates,
)
from backend.data_pipeline.validation.freshness_checker import (
    check_pre_match_freshness, should_block_prediction,
)
from backend.prediction_engine.models.outcome_model import (
    OutcomeModelInput, predict_outcome,
)
from backend.prediction_engine.models.score_model import (
    ScoreModelInput, predict_scorelines,
)
from backend.prediction_engine.engines.confidence_engine import (
    ConfidenceInput, compute_confidence,
)
from backend.prediction_engine.engines.risk_engine import (
    RiskInput, compute_risk,
)
from backend.prediction_engine.engines.value_engine import (
    ValueInput, compute_value,
)
from backend.prediction_engine.engines.explanation_engine import (
    ExplanationInput, build_explanation,
)


def _pick_best_bet(
    outcome,
    score_out,
    confidence: float,
) -> str:
    """Choose the recommended bet type from available outputs."""
    home_p  = outcome.home_win_probability
    draw_p  = outcome.draw_probability
    away_p  = outcome.away_win_probability
    over_p  = score_out.over_2_5_probability
    btts_p  = score_out.btts_probability

    if confidence < 45:
        return "No Bet Recommended"

    # Over 2.5 goals
    if over_p >= 0.58 and score_out.home_xg + score_out.away_xg >= 2.8:
        return "Over 2.5 Goals"

    # Strong home favourite → Draw No Bet reduces draw risk
    if home_p >= 0.52 and draw_p >= 0.22:
        return f"Home Win — Draw No Bet"

    # Strong away → Draw No Bet
    if away_p >= 0.52 and draw_p >= 0.22:
        return f"Away Win — Draw No Bet"

    # Clear home win
    if home_p >= 0.58:
        return "Home Win"

    # Clear away win
    if away_p >= 0.52:
        return "Away Win"

    # BTTS
    if btts_p >= 0.60:
        return "Both Teams to Score"

    # Under 2.5 (low xG game)
    if score_out.home_xg + score_out.away_xg <= 2.0:
        return "Under 2.5 Goals"

    if confidence < 55:
        return "No Bet Recommended"

    return "Home Win" if home_p > away_p else "Away Win"


async def generate_prediction(
    db: AsyncSession,
    match_id: int,
) -> Prediction | None:
    """
    Full prediction pipeline for one match.
    Returns the saved Prediction object, or None if blocked.
    """
    # ── Load match + related data ────────────────────────────────────────
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        return None

    home_result = await db.execute(select(Team).where(Team.id == match.home_team_id))
    away_result = await db.execute(select(Team).where(Team.id == match.away_team_id))
    league_result = await db.execute(select(League).where(League.id == match.league_id))

    home_team  = home_result.scalar_one_or_none()
    away_team  = away_result.scalar_one_or_none()
    league     = league_result.scalar_one_or_none()

    if not home_team or not away_team or not league:
        return None

    # ── Latest snapshot + freshness ─────────────────────────────────────
    snap_result = await db.execute(
        select(MatchDataSnapshot)
        .where(MatchDataSnapshot.match_id == match_id)
        .order_by(MatchDataSnapshot.collected_at.desc())
        .limit(1)
    )
    snapshot = snap_result.scalar_one_or_none()

    freshness = check_pre_match_freshness(
        odds_updated_at   = snapshot.odds_updated_at if snapshot else None,
        injury_updated_at = snapshot.injury_updated_at if snapshot else None,
        lineup_updated_at = snapshot.lineup_updated_at if snapshot else None,
        stats_updated_at  = snapshot.stats_updated_at if snapshot else None,
    )

    if should_block_prediction(freshness):
        print(f"  ! Match {match_id}: prediction blocked — freshness={freshness.value}")
        return None

    # ── Build team features ──────────────────────────────────────────────
    print(f"  Building features for {home_team.name} vs {away_team.name} …")
    home_metrics = await build_team_metrics(db, home_team, league.slug, match.kickoff_time, is_home=True)
    away_metrics = await build_team_metrics(db, away_team, league.slug, match.kickoff_time, is_home=False)

    # ── Outcome model ────────────────────────────────────────────────────
    outcome = predict_outcome(OutcomeModelInput(
        home=home_metrics,
        away=away_metrics,
        odds_movement_score=0.0,   # will be updated once odds pipeline is live
    ))

    # ── Score model ──────────────────────────────────────────────────────
    home_xg, away_xg = await build_xg_estimates(
        league.slug, home_team.name, away_team.name
    )
    score_out = predict_scorelines(ScoreModelInput(home_xg=home_xg, away_xg=away_xg))

    # ── Confidence ───────────────────────────────────────────────────────
    dominant_prob = max(
        outcome.home_win_probability,
        outcome.draw_probability,
        outcome.away_win_probability,
    )
    raw_conf = round(dominant_prob * 100, 1)

    # Pull odds from snapshot if available
    raw_data = {}
    if snapshot and snapshot.raw_data:
        try:
            raw_data = json.loads(snapshot.raw_data)
        except (json.JSONDecodeError, TypeError):
            pass

    # Compute implied probability for the most likely outcome
    if outcome.home_win_probability >= outcome.away_win_probability:
        best_odds = raw_data.get("home_odds", 0)
    else:
        best_odds = raw_data.get("away_odds", 0)

    implied_prob = round(100 / best_odds, 1) if best_odds > 1 else dominant_prob * 100
    model_edge = raw_conf - implied_prob

    conf_result = compute_confidence(ConfidenceInput(
        raw_model_probability   = raw_conf,
        freshness_status        = freshness,
        lineups_confirmed       = snapshot.lineup_updated_at is not None if snapshot else False,
        odds_moving_heavily     = False,
        model_edge              = model_edge,
        league_accuracy         = 0.52,   # updated by learning loop in Milestone 6
    ))
    final_confidence = conf_result["final_confidence"]

    # ── Pick best bet ─────────────────────────────────────────────────────
    recommended_bet = _pick_best_bet(outcome, score_out, final_confidence)

    # ── Risk ─────────────────────────────────────────────────────────────
    risk_result = compute_risk(RiskInput(
        bet_type            = recommended_bet.lower().replace(" ", "_").replace("—_", ""),
        draw_probability    = outcome.draw_probability,
        confidence          = final_confidence,
        lineups_confirmed   = conf_result["penalties"].get("lineup_uncertainty") == 0,
        odds_moving_heavily = False,
        is_live             = False,
        away_scoring_rate   = 0.6,   # placeholder; feature builder will populate
    ))

    # ── Value ─────────────────────────────────────────────────────────────
    ref_odds = best_odds if best_odds > 1 else 2.0
    value_result = compute_value(ValueInput(
        model_probability = raw_conf,
        bookmaker_odds    = ref_odds,
    ))

    # ── Explanation ───────────────────────────────────────────────────────
    explanation = build_explanation(ExplanationInput(
        home_team       = home_team.name,
        away_team       = away_team.name,
        recommended_bet = recommended_bet,
        home_win_prob   = outcome.home_win_probability,
        draw_prob       = outcome.draw_probability,
        away_win_prob   = outcome.away_win_probability,
        home_xg         = home_xg,
        away_xg         = away_xg,
        confidence      = final_confidence,
        risk_level      = risk_result["risk_level"],
        value_gap       = value_result["value_gap"],
        freshness_status = freshness,
        lineups_confirmed = snapshot.lineup_updated_at is not None if snapshot else False,
        home_form_score = home_metrics.recent_form_score,
        away_form_score = away_metrics.recent_form_score,
        risk_reasons    = risk_result["risk_reasons"],
        is_live         = False,
    ))

    # ── Save Prediction ───────────────────────────────────────────────────
    pred = Prediction(
        match_id             = match_id,
        data_snapshot_id     = snapshot.id if snapshot else None,
        generated_at         = datetime.now(timezone.utc),
        mode                 = PredictionMode.PRE_MATCH,
        recommended_bet      = recommended_bet,
        expected_score       = score_out.most_likely_score,
        home_win_probability = outcome.home_win_probability,
        draw_probability     = outcome.draw_probability,
        away_win_probability = outcome.away_win_probability,
        home_xg              = home_xg,
        away_xg              = away_xg,
        confidence_score     = final_confidence,
        risk_level           = risk_result["risk_level"],
        value_rating         = value_result["value_rating"],
        explanation          = explanation,
        data_freshness_status = freshness,
        lineups_confirmed    = snapshot.lineup_updated_at is not None if snapshot else False,
        prediction_status    = "active",
    )
    db.add(pred)
    await db.flush()

    # Save scoreline probabilities
    for s in score_out.top_scorelines:
        db.add(ScorelineProbability(
            prediction_id = pred.id,
            home_goals    = s.home_goals,
            away_goals    = s.away_goals,
            probability   = s.probability,
        ))

    await db.commit()
    print(f"  ✓ Prediction saved: {home_team.name} vs {away_team.name} → {recommended_bet} ({final_confidence:.0f}%)")
    return pred
