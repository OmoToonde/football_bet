"""
Champions League Module Orchestrator — Milestone 7
Handles CL-specific prediction requests:
  - Single match (via standard predictor with CL adjustments)
  - Two-legged tie qualification probability
  - Tournament winner simulation
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.champions_league.cross_league_strength import (
    compare_teams, adjusted_team_strength, league_multiplier,
)
from backend.champions_league.two_leg_predictor import (
    TwoLegInput, TwoLegOutput, simulate_two_legs,
)
from backend.champions_league.tournament_simulator import (
    CLTeam, SimulationResult, run_tournament_simulation, DEFAULT_CL_TEAMS,
)
from backend.prediction_engine.models.score_model import ScoreModelInput, predict_scorelines


@dataclass
class CLMatchPrediction:
    home_team: str
    away_team: str
    home_league: str
    away_league: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    home_xg: float
    away_xg: float
    expected_score: str
    home_adjusted_strength: float
    away_adjusted_strength: float
    cross_league_note: str


def predict_cl_match(
    home_team: str,
    home_strength: float,
    home_league: str,
    away_team: str,
    away_strength: float,
    away_league: str,
) -> CLMatchPrediction:
    """Single CL match prediction with cross-league strength adjustment."""
    comp = compare_teams(home_team, home_strength, home_league,
                         away_team, away_strength, away_league)

    h_adj = comp["home_adjusted_strength"]
    a_adj = comp["away_adjusted_strength"]

    # xG from adjusted strength
    base_xg = 1.35
    home_xg = round(base_xg * (h_adj / max(0.1, a_adj)) * 1.05, 2)
    away_xg = round(base_xg * (a_adj / max(0.1, h_adj)), 2)
    home_xg = max(0.3, min(4.0, home_xg))
    away_xg = max(0.2, min(3.5, away_xg))

    score_out = predict_scorelines(ScoreModelInput(home_xg=home_xg, away_xg=away_xg))

    h_mult = league_multiplier(home_league)
    a_mult = league_multiplier(away_league)
    if abs(h_mult - a_mult) > 0.2:
        stronger_league = home_league if h_mult > a_mult else away_league
        weaker_league   = away_league if h_mult > a_mult else home_league
        note = (
            f"{stronger_league.replace('-', ' ').title()} is a significantly stronger league than "
            f"{weaker_league.replace('-', ' ').title()} "
            f"(UEFA coefficients: {h_mult:.2f}× vs {a_mult:.2f}×). "
            "This has been factored into the strength comparison."
        )
    else:
        note = "Both teams come from similarly rated leagues — domestic form is the primary differentiator."

    return CLMatchPrediction(
        home_team               = home_team,
        away_team               = away_team,
        home_league             = home_league,
        away_league             = away_league,
        home_win_prob           = comp["home_win"],
        draw_prob               = comp["draw"],
        away_win_prob           = comp["away_win"],
        home_xg                 = home_xg,
        away_xg                 = away_xg,
        expected_score          = score_out.most_likely_score,
        home_adjusted_strength  = h_adj,
        away_adjusted_strength  = a_adj,
        cross_league_note       = note,
    )


def predict_two_leg_tie(
    home_team: str,
    home_strength: float,
    home_league: str,
    away_team: str,
    away_strength: float,
    away_league: str,
    first_leg_home: int | None = None,
    first_leg_away: int | None = None,
) -> TwoLegOutput:
    """Two-legged tie qualification probabilities."""
    return simulate_two_legs(TwoLegInput(
        home_team             = home_team,
        home_strength         = home_strength,
        home_league           = home_league,
        away_team             = away_team,
        away_strength         = away_strength,
        away_league           = away_league,
        first_leg_home_score  = first_leg_home,
        first_leg_away_score  = first_leg_away,
    ))


def run_cl_simulation(
    teams: list[CLTeam] | None = None,
    simulations: int = 10_000,
) -> SimulationResult:
    """Full tournament Monte Carlo simulation."""
    return run_tournament_simulation(teams or DEFAULT_CL_TEAMS, simulations)
