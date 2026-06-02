"""
Live State Processor — Milestone 3
Converts a LiveMatchState into in-play probability updates.

Pipeline:
  LiveMatchState + pre-match Prediction
  → adjust_for_score_and_time()
  → adjust_for_red_cards()
  → LiveProbabilities
  → LiveRecommendation or No Live Bet
"""
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.db.models import (
    LiveMatchState, Prediction, FreshnessStatus, RiskLevel,
)
from backend.data_pipeline.validation.freshness_checker import (
    check_live_freshness, should_block_live_recommendation,
)
from backend.prediction_engine.models.score_model import (
    ScoreModelInput, predict_scorelines,
)


@dataclass
class LiveProbabilities:
    home_win: float
    draw: float
    away_win: float
    over_remaining: float       # prob that remaining goals > threshold
    btts_still_possible: bool
    live_home_xg: float
    live_away_xg: float
    expected_final_home: int
    expected_final_away: int
    blocked: bool               # True if live data is too stale to trust
    block_reason: str


FULL_MATCH_MINUTES = 90


def _time_remaining(minute: int) -> float:
    """Fraction of match remaining (0 = FT, 1 = kickoff)."""
    return max(0.0, (FULL_MATCH_MINUTES - minute) / FULL_MATCH_MINUTES)


def _score_to_probs(goal_diff: int, time_rem: float) -> tuple[float, float, float]:
    """
    Rough probability adjustment based on current goal difference and time left.
    Uses a sigmoid-style curve — the bigger the lead and less time, the more
    confident the leading team wins.
    """
    if time_rem <= 0:
        if goal_diff > 0:
            return 1.0, 0.0, 0.0
        elif goal_diff < 0:
            return 0.0, 0.0, 1.0
        else:
            return 0.0, 1.0, 0.0

    # Base swing per goal and per unit time
    swing = min(0.35, abs(goal_diff) * 0.20 * (1 - time_rem))

    if goal_diff == 0:
        # Even game — draw probability rises with less time
        draw_p = 0.25 + (1 - time_rem) * 0.20
        home_p = (1 - draw_p) / 2
        away_p = home_p
    elif goal_diff > 0:
        # Home leading
        home_p = 0.50 + swing
        draw_p = max(0.05, 0.25 - swing * 0.5)
        away_p = max(0.05, 1 - home_p - draw_p)
    else:
        # Away leading
        away_p = 0.50 + swing
        draw_p = max(0.05, 0.25 - swing * 0.5)
        home_p = max(0.05, 1 - away_p - draw_p)

    total = home_p + draw_p + away_p
    return round(home_p / total, 3), round(draw_p / total, 3), round(away_p / total, 3)


def _red_card_adjustment(
    home_p: float, draw_p: float, away_p: float,
    red_home: int, red_away: int,
) -> tuple[float, float, float]:
    """Apply probability penalty for red cards (each = ~0.12 swing)."""
    net = (red_away - red_home) * 0.12  # positive = helps home
    home_p = min(0.92, max(0.04, home_p + net))
    away_p = min(0.92, max(0.04, away_p - net))
    draw_p = max(0.04, 1 - home_p - away_p)
    total = home_p + draw_p + away_p
    return round(home_p / total, 3), round(draw_p / total, 3), round(away_p / total, 3)


def process_live_state(
    state: LiveMatchState,
    pre_match_pred: Prediction,
    score_updated_at: datetime | None = None,
    odds_updated_at: datetime | None = None,
    stats_updated_at: datetime | None = None,
) -> LiveProbabilities:
    """
    Core live processor. Returns updated probabilities given current match state.
    """
    # ── Freshness gate ────────────────────────────────────────────────────
    freshness = check_live_freshness(
        score_updated_at = score_updated_at or state.collected_at,
        odds_updated_at  = odds_updated_at  or state.live_odds_updated_at,
        stats_updated_at = stats_updated_at or state.collected_at,
    )
    if should_block_live_recommendation(freshness):
        return LiveProbabilities(
            home_win=0, draw=0, away_win=0,
            over_remaining=0, btts_still_possible=False,
            live_home_xg=0, live_away_xg=0,
            expected_final_home=state.home_score,
            expected_final_away=state.away_score,
            blocked=True,
            block_reason=(
                "Live odds feed is delayed" if freshness == FreshnessStatus.LIVE_DELAYED
                else "Live event feed is delayed"
            ),
        )

    minute   = state.match_minute or 0
    h_score  = state.home_score
    a_score  = state.away_score
    goal_diff = h_score - a_score
    time_rem  = _time_remaining(minute)

    # ── Score-based probability ───────────────────────────────────────────
    home_p, draw_p, away_p = _score_to_probs(goal_diff, time_rem)

    # ── Blend with pre-match prediction (more weight as time increases) ───
    pre_weight = time_rem * 0.30   # up to 30% pre-match influence at kickoff
    live_weight = 1 - pre_weight
    if pre_match_pred:
        home_p = live_weight * home_p + pre_weight * (pre_match_pred.home_win_probability or 0.34)
        draw_p = live_weight * draw_p + pre_weight * (pre_match_pred.draw_probability or 0.33)
        away_p = live_weight * away_p + pre_weight * (pre_match_pred.away_win_probability or 0.33)

    # ── Red card adjustment ───────────────────────────────────────────────
    home_p, draw_p, away_p = _red_card_adjustment(
        home_p, draw_p, away_p,
        state.red_cards_home, state.red_cards_away,
    )

    # ── Expected remaining goals (Poisson from live xG rates) ────────────
    live_xg_home = state.live_xg_home or (pre_match_pred.home_xg or 1.4) * time_rem
    live_xg_away = state.live_xg_away or (pre_match_pred.away_xg or 1.1) * time_rem

    # Remaining xG scales with time left
    remaining_xg_home = live_xg_home * time_rem
    remaining_xg_away = live_xg_away * time_rem

    score_out = predict_scorelines(ScoreModelInput(
        home_xg=max(0.05, remaining_xg_home),
        away_xg=max(0.05, remaining_xg_away),
    ))

    expected_final_home = h_score + round(remaining_xg_home)
    expected_final_away = a_score + round(remaining_xg_away)

    # Over remaining 0.5 goals probability
    over_rem = sum(
        s.probability for s in score_out.top_scorelines
        if s.home_goals + s.away_goals >= 1
    )

    # BTTS still possible?
    btts_possible = (a_score == 0 or h_score == 0) and time_rem > 0.15

    return LiveProbabilities(
        home_win=home_p,
        draw=draw_p,
        away_win=away_p,
        over_remaining=round(over_rem, 3),
        btts_still_possible=btts_possible,
        live_home_xg=round(live_xg_home, 2),
        live_away_xg=round(live_xg_away, 2),
        expected_final_home=expected_final_home,
        expected_final_away=expected_final_away,
        blocked=False,
        block_reason="",
    )


def pick_live_bet(live: LiveProbabilities, minute: int) -> dict:
    """
    Choose a live bet recommendation from updated probabilities.
    All live bets are labelled Live High Risk per PRD requirements.
    """
    if live.blocked:
        return {
            "recommended_bet": "No Live Bet Recommended",
            "risk_level": RiskLevel.NO_BET,
            "reason": f"No live bet recommended. Reason: {live.block_reason}.",
        }

    time_rem = _time_remaining(minute)

    # Too little time for a meaningful bet
    if time_rem < 0.10:
        return {
            "recommended_bet": "No Live Bet Recommended",
            "risk_level": RiskLevel.NO_BET,
            "reason": "Less than 9 minutes remaining — insufficient time for a reliable recommendation.",
        }

    h, d, a = live.home_win, live.draw, live.away_win

    if live.over_remaining >= 0.65 and time_rem > 0.25:
        bet = "Next Goal — Over 0.5 Remaining Goals"
    elif h >= 0.70:
        bet = "Live Home Win"
    elif a >= 0.65:
        bet = "Live Away Win"
    elif d >= 0.55 and time_rem < 0.20:
        bet = "Live Draw"
    elif live.btts_still_possible and live.over_remaining >= 0.55:
        bet = "Both Teams to Score"
    elif h >= 0.55:
        bet = "Live Home Win — Draw No Bet"
    elif a >= 0.50:
        bet = "Live Away Win — Draw No Bet"
    else:
        return {
            "recommended_bet": "No Live Bet Recommended",
            "risk_level": RiskLevel.NO_BET,
            "reason": "No clear live edge at this stage of the match.",
        }

    return {
        "recommended_bet": bet,
        "risk_level": RiskLevel.LIVE_HIGH_RISK,
        "reason": (
            f"Live update at {minute}': "
            f"home {h:.0%} / draw {d:.0%} / away {a:.0%}. "
            f"Live recommendations carry elevated risk — odds move within seconds."
        ),
    }
