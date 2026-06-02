"""
Tests for the live state processor.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest

from backend.prediction_engine.live.live_state_processor import (
    process_live_state, pick_live_bet, _score_to_probs, _red_card_adjustment,
)
from backend.db.models import RiskLevel, FreshnessStatus


def _mock_state(minute=60, home=1, away=0, red_h=0, red_a=0, live_xg_h=None, live_xg_a=None):
    state = MagicMock()
    state.match_minute = minute
    state.home_score = home
    state.away_score = away
    state.red_cards_home = red_h
    state.red_cards_away = red_a
    state.live_xg_home = live_xg_h
    state.live_xg_away = live_xg_a
    state.collected_at = datetime.now(timezone.utc)
    state.live_odds_updated_at = datetime.now(timezone.utc)
    state.event_feed_freshness = FreshnessStatus.FRESH
    return state


def _mock_pred(h=0.48, d=0.27, a=0.25, h_xg=1.5, a_xg=1.1):
    pred = MagicMock()
    pred.home_win_probability = h
    pred.draw_probability = d
    pred.away_win_probability = a
    pred.home_xg = h_xg
    pred.away_xg = a_xg
    return pred


def _fresh_times():
    now = datetime.now(timezone.utc)
    return now, now, now


class TestScoreToProbs:
    def test_level_game_balanced(self):
        h, d, a = _score_to_probs(0, 0.5)
        assert abs(h - a) < 0.05

    def test_home_lead_favours_home(self):
        h, d, a = _score_to_probs(2, 0.2)
        assert h > a

    def test_away_lead_favours_away(self):
        h, d, a = _score_to_probs(-1, 0.3)
        assert a > h

    def test_probs_sum_to_one(self):
        for diff in [-2, -1, 0, 1, 2]:
            h, d, a = _score_to_probs(diff, 0.4)
            assert abs(h + d + a - 1.0) < 0.001


class TestRedCardAdjustment:
    def test_home_red_card_hurts_home(self):
        h0, d0, a0 = 0.5, 0.25, 0.25
        h, d, a = _red_card_adjustment(h0, d0, a0, red_home=1, red_away=0)
        assert h < h0

    def test_away_red_card_hurts_away(self):
        h0, d0, a0 = 0.5, 0.25, 0.25
        h, d, a = _red_card_adjustment(h0, d0, a0, red_home=0, red_away=1)
        assert h > h0

    def test_probs_still_sum_to_one(self):
        h, d, a = _red_card_adjustment(0.5, 0.25, 0.25, 1, 0)
        assert abs(h + d + a - 1.0) < 0.001


class TestProcessLiveState:
    def test_blocked_when_score_stale(self):
        state = _mock_state()
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        result = process_live_state(
            state, _mock_pred(),
            score_updated_at=stale_time,
            odds_updated_at=datetime.now(timezone.utc),
        )
        assert result.blocked is True

    def test_not_blocked_with_fresh_data(self):
        now = datetime.now(timezone.utc)
        state = _mock_state()
        result = process_live_state(state, _mock_pred(), now, now, now)
        assert result.blocked is False

    def test_home_lead_late_increases_home_prob(self):
        now = datetime.now(timezone.utc)
        state = _mock_state(minute=80, home=2, away=0)
        result = process_live_state(state, _mock_pred(), now, now, now)
        assert result.home_win > result.away_win

    def test_away_lead_increases_away_prob(self):
        now = datetime.now(timezone.utc)
        state = _mock_state(minute=70, home=0, away=1)
        result = process_live_state(state, _mock_pred(), now, now, now)
        assert result.away_win > result.home_win

    def test_probs_sum_to_one(self):
        now = datetime.now(timezone.utc)
        state = _mock_state(minute=45, home=0, away=0)
        result = process_live_state(state, _mock_pred(), now, now, now)
        assert abs(result.home_win + result.draw + result.away_win - 1.0) < 0.005


class TestPickLiveBet:
    def _live(self, h=0.75, d=0.15, a=0.10, blocked=False):
        lp = MagicMock()
        lp.home_win = h
        lp.draw = d
        lp.away_win = a
        lp.over_remaining = 0.55
        lp.btts_still_possible = True
        lp.blocked = blocked
        lp.block_reason = "stale" if blocked else ""
        return lp

    def test_blocked_returns_no_bet(self):
        result = pick_live_bet(self._live(blocked=True), minute=50)
        assert result["recommended_bet"] == "No Live Bet Recommended"

    def test_late_game_no_bet(self):
        result = pick_live_bet(self._live(), minute=88)
        assert result["recommended_bet"] == "No Live Bet Recommended"

    def test_strong_home_lead_recommends_home(self):
        result = pick_live_bet(self._live(h=0.80, d=0.12, a=0.08), minute=60)
        assert "Home" in result["recommended_bet"]

    def test_live_bets_are_high_risk(self):
        result = pick_live_bet(self._live(h=0.75), minute=50)
        if result["recommended_bet"] != "No Live Bet Recommended":
            assert result["risk_level"] == RiskLevel.LIVE_HIGH_RISK
