"""
Live-Feed Simulation — Milestone 8
Drives the live state processor through a realistic sequence of in-play events
to verify Live Match Mode end-to-end: probability updates, red-card swings,
freshness gating, and the live bet picker.

Usage: python -m scripts.simulate_live_feed
"""
import sys, os
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.prediction_engine.live.live_state_processor import (
    process_live_state, pick_live_bet,
)
from backend.db.models import FreshnessStatus


def make_state(minute, hs, as_, rh=0, ra=0, xgh=None, xga=None, odds_age_s=2):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        match_minute=minute, home_score=hs, away_score=as_,
        red_cards_home=rh, red_cards_away=ra,
        substitutions_home=0, substitutions_away=0,
        live_xg_home=xgh, live_xg_away=xga,
        collected_at=now,
        live_odds_updated_at=now - timedelta(seconds=odds_age_s),
        event_feed_freshness=FreshnessStatus.FRESH,
    )


def make_pred():
    return SimpleNamespace(
        home_win_probability=0.48, draw_probability=0.27, away_win_probability=0.25,
        home_xg=1.6, away_xg=1.1,
    )


# Simulated match timeline: (minute, home_score, away_score, red_home, red_away, note)
TIMELINE = [
    (5,  0, 0, 0, 0, "Kickoff phase"),
    (25, 1, 0, 0, 0, "Home scores"),
    (40, 1, 1, 0, 0, "Away equalises"),
    (55, 1, 1, 0, 1, "Away red card"),
    (70, 2, 1, 0, 1, "Home retakes lead"),
    (85, 2, 1, 0, 1, "Closing stages"),
]


def main():
    print("=== Live-Feed Simulation: Arsenal vs Chelsea ===\n")
    pred = make_pred()

    for minute, hs, as_, rh, ra, note in TIMELINE:
        state = make_state(minute, hs, as_, rh, ra,
                           xgh=1.4 * (minute / 90), xga=1.0 * (minute / 90))
        live = process_live_state(
            state, pred,
            score_updated_at=state.collected_at,
            odds_updated_at=state.live_odds_updated_at,
            stats_updated_at=state.collected_at,
        )
        bet = pick_live_bet(live, minute)

        print(f"{minute}' [{hs}-{as_}] {note}")
        if live.blocked:
            print(f"     BLOCKED: {live.block_reason}")
        else:
            print(f"     Home {live.home_win:.0%} / Draw {live.draw:.0%} / Away {live.away_win:.0%}")
            print(f"     Bet: {bet['recommended_bet']} [{bet['risk_level'].value}]")
        print()

    # Test freshness gating: stale odds feed
    print("--- Freshness gate test (stale 20s odds) ---")
    stale = make_state(60, 1, 0, odds_age_s=20)
    live = process_live_state(
        stale, pred,
        score_updated_at=stale.collected_at,
        odds_updated_at=stale.live_odds_updated_at,
        stats_updated_at=stale.collected_at,
    )
    bet = pick_live_bet(live, 60)
    print(f"     Blocked: {live.blocked} — {bet['recommended_bet']}")
    assert live.blocked, "Stale odds should block the live recommendation"
    print("     PASS: stale live odds correctly blocked\n")

    print("=== Live-feed simulation complete ===")


if __name__ == "__main__":
    main()
