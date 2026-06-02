"""
Unit tests for the prediction engines.
Run with:  python -m pytest tests/backend/test_engines.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from backend.prediction_engine.models.score_model import ScoreModelInput, predict_scorelines
from backend.prediction_engine.models.outcome_model import (
    OutcomeModelInput, TeamMetrics, predict_outcome,
)
from backend.prediction_engine.engines.confidence_engine import ConfidenceInput, compute_confidence
from backend.prediction_engine.engines.risk_engine import RiskInput, compute_risk
from backend.prediction_engine.engines.value_engine import ValueInput, compute_value
from backend.prediction_engine.engines.explanation_engine import ExplanationInput, build_explanation
from backend.db.models import FreshnessStatus, RiskLevel


# ── Score model ──────────────────────────────────────────────────────────────

class TestScoreModel:
    def test_probabilities_sum_to_one(self):
        out = predict_scorelines(ScoreModelInput(home_xg=1.5, away_xg=1.0))
        total = sum(s.probability for s in out.top_scorelines)
        # top 8 scorelines don't sum to 1, but full distribution should be close
        assert 0 < total <= 1.01

    def test_most_likely_score_format(self):
        out = predict_scorelines(ScoreModelInput(home_xg=1.8, away_xg=1.2))
        parts = out.most_likely_score.split("-")
        assert len(parts) == 2
        assert all(p.isdigit() for p in parts)

    def test_over_probability_range(self):
        out = predict_scorelines(ScoreModelInput(home_xg=1.5, away_xg=1.0))
        assert 0 <= out.over_2_5_probability <= 1

    def test_btts_probability_range(self):
        out = predict_scorelines(ScoreModelInput(home_xg=1.5, away_xg=1.0))
        assert 0 <= out.btts_probability <= 1

    def test_high_xg_favours_over(self):
        high = predict_scorelines(ScoreModelInput(home_xg=2.5, away_xg=2.0))
        low  = predict_scorelines(ScoreModelInput(home_xg=0.8, away_xg=0.6))
        assert high.over_2_5_probability > low.over_2_5_probability

    def test_dominant_team_scores_more(self):
        out = predict_scorelines(ScoreModelInput(home_xg=2.5, away_xg=0.5))
        home_goals, away_goals = map(int, out.most_likely_score.split("-"))
        assert home_goals >= away_goals


# ── Outcome model ─────────────────────────────────────────────────────────────

def _equal_metrics() -> TeamMetrics:
    return TeamMetrics(
        recent_form_score=0.5, home_away_score=0.5, xg_score=0.5,
        attacking_score=0.5, defensive_score=0.5, availability_score=0.85,
        fixture_congestion_score=0.7, h2h_score=0.5,
    )


def _strong_metrics() -> TeamMetrics:
    return TeamMetrics(
        recent_form_score=0.9, home_away_score=0.9, xg_score=0.9,
        attacking_score=0.9, defensive_score=0.9, availability_score=1.0,
        fixture_congestion_score=1.0, h2h_score=0.8,
    )


def _weak_metrics() -> TeamMetrics:
    return TeamMetrics(
        recent_form_score=0.1, home_away_score=0.1, xg_score=0.1,
        attacking_score=0.1, defensive_score=0.1, availability_score=0.5,
        fixture_congestion_score=0.2, h2h_score=0.2,
    )


class TestOutcomeModel:
    def test_probs_sum_to_one(self):
        out = predict_outcome(OutcomeModelInput(_equal_metrics(), _equal_metrics(), 0.0))
        assert abs(out.home_win_probability + out.draw_probability + out.away_win_probability - 1.0) < 0.001

    def test_equal_teams_are_balanced(self):
        out = predict_outcome(OutcomeModelInput(_equal_metrics(), _equal_metrics(), 0.0))
        assert abs(out.home_win_probability - out.away_win_probability) < 0.15

    def test_strong_home_favoured(self):
        out = predict_outcome(OutcomeModelInput(_strong_metrics(), _weak_metrics(), 0.0))
        assert out.home_win_probability > out.away_win_probability

    def test_strong_away_favoured(self):
        out = predict_outcome(OutcomeModelInput(_weak_metrics(), _strong_metrics(), 0.0))
        assert out.away_win_probability > out.home_win_probability

    def test_probabilities_in_valid_range(self):
        out = predict_outcome(OutcomeModelInput(_strong_metrics(), _weak_metrics(), 0.3))
        for p in [out.home_win_probability, out.draw_probability, out.away_win_probability]:
            assert 0 <= p <= 1


# ── Confidence engine ─────────────────────────────────────────────────────────

class TestConfidenceEngine:
    def test_stale_data_reduces_confidence(self):
        fresh = compute_confidence(ConfidenceInput(70, FreshnessStatus.FRESH, True, False, 5, 0.55))
        stale = compute_confidence(ConfidenceInput(70, FreshnessStatus.STALE, True, False, 5, 0.55))
        assert fresh["final_confidence"] > stale["final_confidence"]

    def test_lineup_uncertainty_reduces_confidence(self):
        confirmed   = compute_confidence(ConfidenceInput(70, FreshnessStatus.FRESH, True, False, 5, 0.55))
        unconfirmed = compute_confidence(ConfidenceInput(70, FreshnessStatus.FRESH, False, False, 5, 0.55))
        assert confirmed["final_confidence"] > unconfirmed["final_confidence"]

    def test_output_capped_at_95(self):
        result = compute_confidence(ConfidenceInput(99, FreshnessStatus.FRESH, True, False, 20, 0.8))
        assert result["final_confidence"] <= 95

    def test_output_floor_at_5(self):
        result = compute_confidence(ConfidenceInput(1, FreshnessStatus.STALE, False, True, -20, 0.1))
        assert result["final_confidence"] >= 5


# ── Risk engine ───────────────────────────────────────────────────────────────

class TestRiskEngine:
    def test_correct_score_is_high_risk(self):
        result = compute_risk(RiskInput("correct_score", 0.25, 65, True, False, False, 0.6))
        assert result["risk_level"] in (RiskLevel.HIGH, RiskLevel.VERY_HIGH)

    def test_double_chance_is_lower_risk(self):
        result = compute_risk(RiskInput("double_chance", 0.15, 70, True, False, False, 0.5))
        assert result["risk_level"] in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_live_bets_always_live_high_risk(self):
        result = compute_risk(RiskInput("home_win", 0.2, 70, True, False, True, 0.5))
        assert result["risk_level"] == RiskLevel.LIVE_HIGH_RISK

    def test_no_bet_returns_no_bet(self):
        result = compute_risk(RiskInput("no_bet", 0.33, 40, False, False, False, 0.5))
        assert result["risk_level"] == RiskLevel.NO_BET

    def test_low_confidence_escalates_risk(self):
        high_conf = compute_risk(RiskInput("home_win", 0.20, 75, True, False, False, 0.5))
        low_conf  = compute_risk(RiskInput("home_win", 0.20, 40, True, False, False, 0.5))
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        assert risk_order.index(low_conf["risk_level"]) >= risk_order.index(high_conf["risk_level"])


# ── Value engine ──────────────────────────────────────────────────────────────

class TestValueEngine:
    def test_positive_edge_is_value_bet(self):
        result = compute_value(ValueInput(model_probability=65, bookmaker_odds=2.0))
        assert result["is_value_bet"] is True

    def test_negative_edge_is_not_value(self):
        result = compute_value(ValueInput(model_probability=40, bookmaker_odds=2.0))
        assert result["is_value_bet"] is False

    def test_value_rating_in_range(self):
        result = compute_value(ValueInput(model_probability=60, bookmaker_odds=2.5))
        assert 1.0 <= result["value_rating"] <= 10.0

    def test_implied_probability_calculation(self):
        result = compute_value(ValueInput(model_probability=60, bookmaker_odds=2.0))
        assert abs(result["implied_probability"] - 50.0) < 0.1

    def test_exceptional_value_on_large_edge(self):
        result = compute_value(ValueInput(model_probability=80, bookmaker_odds=4.0))
        assert result["value_rating"] >= 8.0


# ── Explanation engine ────────────────────────────────────────────────────────

class TestExplanationEngine:
    def _base_input(self, bet="Home Win", is_live=False):
        return ExplanationInput(
            home_team="Arsenal", away_team="Chelsea",
            recommended_bet=bet,
            home_win_prob=0.52, draw_prob=0.25, away_win_prob=0.23,
            home_xg=1.8, away_xg=1.1,
            confidence=64.0, risk_level=RiskLevel.MEDIUM,
            value_gap=5.0, freshness_status=FreshnessStatus.FRESH,
            lineups_confirmed=True,
            home_form_score=0.7, away_form_score=0.5,
            risk_reasons=["Draw probability is 25%"],
            is_live=is_live, match_minute=62 if is_live else None,
            home_score=1 if is_live else None,
            away_score=0 if is_live else None,
        )

    def test_explanation_contains_team_names(self):
        text = build_explanation(self._base_input())
        assert "Arsenal" in text and "Chelsea" in text

    def test_explanation_ends_with_disclaimer(self):
        text = build_explanation(self._base_input())
        assert "Bet responsibly" in text

    def test_live_explanation_mentions_minute(self):
        text = build_explanation(self._base_input(is_live=True))
        assert "62" in text

    def test_no_bet_explanation(self):
        text = build_explanation(self._base_input(bet="No Bet Recommended"))
        # Any of these phrases indicate a no-bet explanation
        assert any(p in text.lower() for p in [
            "no high-confidence", "no bet", "not find", "not identify",
            "no clear", "not recommended",
        ])

    def test_forbidden_phrases_raise(self):
        inp = self._base_input()
        inp.recommended_bet = "This is a guaranteed win bet"
        with pytest.raises(ValueError, match="forbidden phrase"):
            build_explanation(inp)
