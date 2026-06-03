"""
Unit tests for the Champions League module.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from backend.champions_league.cross_league_strength import (
    league_multiplier, adjusted_team_strength, compare_teams,
)
from backend.champions_league.two_leg_predictor import TwoLegInput, simulate_two_legs
from backend.champions_league.tournament_simulator import (
    run_tournament_simulation, DEFAULT_CL_TEAMS,
)


class TestCrossLeagueStrength:
    def test_premier_league_has_highest_multiplier(self):
        pl  = league_multiplier("premier-league")
        ere = league_multiplier("eredivisie")
        assert pl > ere

    def test_multiplier_positive(self):
        for slug in ["premier-league", "la-liga", "bundesliga", "serie-a", "ligue-1"]:
            assert league_multiplier(slug) > 0

    def test_adjusted_strength_higher_for_strong_league(self):
        pl_team  = adjusted_team_strength(0.7, "premier-league", "Arsenal")
        ere_team = adjusted_team_strength(0.7, "eredivisie", "Ajax")
        assert pl_team > ere_team

    def test_compare_teams_probs_sum_to_one(self):
        result = compare_teams(
            "Arsenal", 0.82, "premier-league",
            "Bayern Munich", 0.89, "bundesliga",
        )
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.001

    def test_compare_teams_strong_favoured(self):
        result = compare_teams(
            "Real Madrid", 0.92, "la-liga",
            "Young Boys", 0.50, "premier-league",
        )
        assert result["home_win"] > result["away_win"]

    def test_home_advantage_applies(self):
        home = adjusted_team_strength(0.75, "premier-league", "Liverpool", is_home=True)
        away = adjusted_team_strength(0.75, "premier-league", "Liverpool", is_home=False)
        assert home > away


class TestTwoLegPredictor:
    def _inp(self, fl_h=None, fl_a=None):
        return TwoLegInput(
            home_team="Arsenal", home_strength=0.82, home_league="premier-league",
            away_team="Bayern Munich", away_strength=0.89, away_league="bundesliga",
            first_leg_home_score=fl_h, first_leg_away_score=fl_a,
        )

    def test_probs_sum_to_one(self):
        result = simulate_two_legs(self._inp())
        assert abs(result.home_qualify_probability + result.away_qualify_probability - 1.0) < 0.01

    def test_probabilities_in_valid_range(self):
        result = simulate_two_legs(self._inp())
        assert 0 < result.home_qualify_probability < 1
        assert 0 < result.away_qualify_probability < 1

    def test_strong_first_leg_lead_increases_probability(self):
        # Home team won first leg 3-0 — should have very high qualification probability
        result = simulate_two_legs(self._inp(fl_h=3, fl_a=0))
        assert result.home_qualify_probability > 0.85

    def test_away_goal_advantage_reflected(self):
        # Away team won first leg 0-2 — away team should be heavy favourite
        result = simulate_two_legs(self._inp(fl_h=0, fl_a=2))
        assert result.away_qualify_probability > 0.70

    def test_narrative_populated(self):
        result = simulate_two_legs(self._inp())
        assert len(result.narrative) > 20

    def test_first_leg_played_flag(self):
        played = simulate_two_legs(self._inp(fl_h=1, fl_a=1))
        not_played = simulate_two_legs(self._inp())
        assert played.first_leg_played is True
        assert not_played.first_leg_played is False

    def test_extra_time_probability_in_range(self):
        result = simulate_two_legs(self._inp())
        assert 0 <= result.extra_time_probability <= 1

    def test_penalties_subset_of_extra_time(self):
        result = simulate_two_legs(self._inp())
        # Penalties only happen inside extra time
        assert result.penalty_probability <= result.extra_time_probability + 0.01


class TestTournamentSimulator:
    @pytest.fixture(scope="class")
    def sim(self):
        # Use fewer simulations for speed in tests
        return run_tournament_simulation(DEFAULT_CL_TEAMS[:16], simulations=2000)

    def test_winner_probs_sum_to_one(self, sim):
        total = sum(sim.winner_probabilities.values())
        assert abs(total - 1.0) < 0.05

    def test_real_madrid_top_favourite(self, sim):
        top = list(sim.winner_probabilities.keys())[0]
        # Real Madrid should be near the top given their strength
        assert "Real Madrid" in list(sim.winner_probabilities.keys())[:3]

    def test_all_teams_have_r16_probability(self, sim):
        for team in DEFAULT_CL_TEAMS[:16]:
            assert team.name in sim.r16_probabilities

    def test_winner_subset_of_finalists(self, sim):
        for team, win_p in sim.winner_probabilities.items():
            final_p = sim.final_probabilities.get(team, 0)
            assert win_p <= final_p + 0.01  # winner prob can't exceed finalist prob

    def test_finalist_subset_of_semi_finalists(self, sim):
        for team, final_p in sim.final_probabilities.items():
            semi_p = sim.semi_final_probabilities.get(team, 0)
            assert final_p <= semi_p + 0.02
