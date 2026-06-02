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
    MatchDataSnapshot, FreshnessStatus, PredictionMode,
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


def _pick_best_bet(outcome, score_out, confidence: float) -> str:
    """
    Select the best bet type based on model outputs.
    Priority: value market > Draw No Bet safety > straight win > goals market > No Bet.
    """
    home_p = outcome.home_win_probability
    draw_p = outcome.draw_probability
    away_p = outcome.away_win_probability
    over_p = score_out.over_2_5_probability
    btts_p = score_out.btts_probability
    total_xg = score_out.home_xg + score_out.away_xg

    if confidence < 45:
        return "No Bet Recommended"

    # Strong goals signal — both xG and over probability agree
    if over_p >= 0.60 and total_xg >= 2.8:
        return "Over 2.5 Goals"

    # Low-scoring match signal
    if (1 - over_p) >= 0.60 and total_xg <= 1.9:
        return "Under 2.5 Goals"

    # Home favourite — use Draw No Bet to hedge draw risk
    if home_p >= 0.52 and draw_p >= 0.20:
        return "Home Win — Draw No Bet"

    # Away favourite — Draw No Bet
    if away_p >= 0.50 and draw_p >= 0.20:
        return "Away Win — Draw No Bet"

    # Clear home win without significant draw risk
    if home_p >= 0.60 and draw_p < 0.20:
        return "Home Win"

    # Clear away win
    if away_p >= 0.55 and draw_p < 0.20:
        return "Away Win"

    # Both teams to score is a reasonable side market
    if btts_p >= 0.62:
        return "Both Teams to Score"

    # Double chance for close matches where one side leans favourite
    if home_p >= 0.45 and home_p > away_p:
        return "Double Chance — Home or Draw"
    if away_p >= 0.42 and away_p > home_p:
        return "Double Chance — Away or Draw"

    if confidence < 52:
        return "No Bet Recommended"

    return "Home Win" if home_p > away_p else "Away Win"


def _bet_type_key(bet: str) -> str:
    """Normalise bet label to a key for risk engine lookup."""
    b = bet.lower()
    if "draw no bet" in b:
        return "draw_no_bet"
    if "over 2.5" in b:
        return "over_2_5"
    if "under 2.5" in b:
        return "under_2_5"
    if "both teams" in b or "btts" in b:
        return "btts"
    if "double chance" in b:
        return "double_chance"
    if "home win" in b:
        return "home_win"
    if "away win" in b:
        return "away_win"
    return "no_bet"


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

    home_team  = (await db.execute(select(Team).where(Team.id == match.home_team_id))).scalar_one_or_none()
    away_team  = (await db.execute(select(Team).where(Team.id == match.away_team_id))).scalar_one_or_none()
    league     = (await db.execute(select(League).where(League.id == match.league_id))).scalar_one_or_none()

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
        print(f"  ! Match {match_id}: blocked — freshness={freshness.value}")
        return None

    # ── Build team features (with H2H and cache) ─────────────────────────
    print(f"  Building features: {home_team.name} vs {away_team.name} …")
    home_metrics = await build_team_metrics(
        db, home_team, league.slug, match.kickoff_time,
        is_home=True, opponent_name=away_team.name,
    )
    away_metrics = await build_team_metrics(
        db, away_team, league.slug, match.kickoff_time,
        is_home=False, opponent_name=home_team.name,
    )

    # ── Outcome model ────────────────────────────────────────────────────
    outcome = predict_outcome(OutcomeModelInput(
        home=home_metrics,
        away=away_metrics,
        odds_movement_score=0.0,
    ))

    # ── Score model ──────────────────────────────────────────────────────
    home_xg, away_xg = await build_xg_estimates(
        league.slug, home_team.name, away_team.name
    )
    score_out = predict_scorelines(ScoreModelInput(home_xg=home_xg, away_xg=away_xg))

    # ── Odds from snapshot ───────────────────────────────────────────────
    raw_data: dict = {}
    if snapshot and snapshot.raw_data:
        try:
            raw_data = json.loads(snapshot.raw_data)
        except (json.JSONDecodeError, TypeError):
            pass

    favoured_home = outcome.home_win_probability >= outcome.away_win_probability
    best_odds = raw_data.get("home_odds" if favoured_home else "away_odds", 0)
    dominant_prob = max(
        outcome.home_win_probability,
        outcome.draw_probability,
        outcome.away_win_probability,
    )
    raw_conf = round(dominant_prob * 100, 1)
    implied_prob = round(100 / best_odds, 1) if best_odds > 1 else raw_conf
    model_edge = raw_conf - implied_prob

    # ── Confidence ───────────────────────────────────────────────────────
    lineups_confirmed = bool(snapshot and snapshot.lineup_updated_at)
    conf_result = compute_confidence(ConfidenceInput(
        raw_model_probability = raw_conf,
        freshness_status      = freshness,
        lineups_confirmed     = lineups_confirmed,
        odds_moving_heavily   = False,
        model_edge            = model_edge,
        league_accuracy       = 0.52,   # refined by learning loop (Milestone 6)
    ))
    final_confidence = conf_result["final_confidence"]

    # ── Bet selection ─────────────────────────────────────────────────────
    recommended_bet = _pick_best_bet(outcome, score_out, final_confidence)

    # ── Away scoring rate from CSV (for risk engine) ─────────────────────
    away_scoring_rate = 0.6
    try:
        from backend.data_pipeline.feature_store.feature_builder import _cached_league_df
        from backend.data_pipeline.ingestion.football_data_co_uk import compute_team_form
        df = _cached_league_df(league.slug)
        af = compute_team_form(df, away_team.name, last_n=10)
        total_games = af.get("games", 1)
        scored_in = sum(
            1 for _, r in df[df["AwayTeam"] == away_team.name].head(10).iterrows()
            if (r.get("FTAG") or 0) > 0
        )
        away_scoring_rate = scored_in / max(1, total_games)
    except Exception:
        pass

    # ── Risk ─────────────────────────────────────────────────────────────
    risk_result = compute_risk(RiskInput(
        bet_type            = _bet_type_key(recommended_bet),
        draw_probability    = outcome.draw_probability,
        confidence          = final_confidence,
        lineups_confirmed   = lineups_confirmed,
        odds_moving_heavily = False,
        is_live             = False,
        away_scoring_rate   = away_scoring_rate,
    ))

    # ── Value ─────────────────────────────────────────────────────────────
    ref_odds = best_odds if best_odds > 1 else 2.0
    value_result = compute_value(ValueInput(
        model_probability = raw_conf,
        bookmaker_odds    = ref_odds,
    ))

    # ── Explanation ───────────────────────────────────────────────────────
    explanation = build_explanation(ExplanationInput(
        home_team         = home_team.name,
        away_team         = away_team.name,
        recommended_bet   = recommended_bet,
        home_win_prob     = outcome.home_win_probability,
        draw_prob         = outcome.draw_probability,
        away_win_prob     = outcome.away_win_probability,
        home_xg           = home_xg,
        away_xg           = away_xg,
        confidence        = final_confidence,
        risk_level        = risk_result["risk_level"],
        value_gap         = value_result["value_gap"],
        freshness_status  = freshness,
        lineups_confirmed = lineups_confirmed,
        home_form_score   = home_metrics.recent_form_score,
        away_form_score   = away_metrics.recent_form_score,
        risk_reasons      = risk_result["risk_reasons"],
        is_live           = False,
    ))

    # ── Persist ───────────────────────────────────────────────────────────
    pred = Prediction(
        match_id              = match_id,
        data_snapshot_id      = snapshot.id if snapshot else None,
        generated_at          = datetime.now(timezone.utc),
        mode                  = PredictionMode.PRE_MATCH,
        recommended_bet       = recommended_bet,
        expected_score        = score_out.most_likely_score,
        home_win_probability  = outcome.home_win_probability,
        draw_probability      = outcome.draw_probability,
        away_win_probability  = outcome.away_win_probability,
        home_xg               = home_xg,
        away_xg               = away_xg,
        confidence_score      = final_confidence,
        risk_level            = risk_result["risk_level"],
        value_rating          = value_result["value_rating"],
        explanation           = explanation,
        data_freshness_status = freshness,
        lineups_confirmed     = lineups_confirmed,
        prediction_status     = "active",
    )
    db.add(pred)
    await db.flush()

    for s in score_out.top_scorelines:
        db.add(ScorelineProbability(
            prediction_id = pred.id,
            home_goals    = s.home_goals,
            away_goals    = s.away_goals,
            probability   = s.probability,
        ))

    await db.commit()
    print(f"  OK {home_team.name} vs {away_team.name} -> {recommended_bet} ({final_confidence:.0f}%)")
    return pred
