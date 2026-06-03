"""
Champions League API Routes — Milestone 7
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.champions_league.cl_module import (
    predict_cl_match, predict_two_leg_tie, run_cl_simulation,
)
from backend.champions_league.tournament_simulator import DEFAULT_CL_TEAMS

router = APIRouter(prefix="/cl", tags=["champions-league"])


# ── Tournament Simulation ───────────────────────────────────────────────────

_cached_simulation = None

@router.get("/simulation")
async def get_tournament_simulation(refresh: bool = False):
    """
    Run (or return cached) Monte Carlo tournament simulation.
    Returns win/final/semi/QF probabilities for all 36 teams.
    """
    global _cached_simulation
    if _cached_simulation is None or refresh:
        result = run_cl_simulation(simulations=20_000)
        _cached_simulation = {
            "simulations": result.simulations_run,
            "winner": result.winner_probabilities,
            "final": result.final_probabilities,
            "semi_final": result.semi_final_probabilities,
            "quarter_final": result.quarter_final_probabilities,
            "round_of_16": result.r16_probabilities,
            "league_phase_top_8": result.league_phase_top8,
        }
    return _cached_simulation


@router.get("/teams")
async def get_cl_teams():
    """Return all CL teams with their strength ratings."""
    return {
        "teams": [
            {
                "name": t.name,
                "league": t.league,
                "domestic_strength": t.domestic_strength,
                "seed": t.seed,
            }
            for t in sorted(DEFAULT_CL_TEAMS, key=lambda x: -x.domestic_strength)
        ]
    }


# ── Match Prediction ─────────────────────────────────────────────────────────

class CLMatchRequest(BaseModel):
    home_team: str
    home_strength: float = 0.75
    home_league: str = "premier-league"
    away_team: str
    away_strength: float = 0.75
    away_league: str = "la-liga"


@router.post("/match-prediction")
async def cl_match_prediction(req: CLMatchRequest):
    """Predict a CL match with cross-league strength adjustment."""
    pred = predict_cl_match(
        req.home_team, req.home_strength, req.home_league,
        req.away_team, req.away_strength, req.away_league,
    )
    return {
        "home_team": pred.home_team,
        "away_team": pred.away_team,
        "home_league": pred.home_league,
        "away_league": pred.away_league,
        "home_win_probability": pred.home_win_prob,
        "draw_probability": pred.draw_prob,
        "away_win_probability": pred.away_win_prob,
        "home_xg": pred.home_xg,
        "away_xg": pred.away_xg,
        "expected_score": pred.expected_score,
        "home_adjusted_strength": pred.home_adjusted_strength,
        "away_adjusted_strength": pred.away_adjusted_strength,
        "cross_league_note": pred.cross_league_note,
        "disclaimer": "Predictions are not guaranteed. Bet responsibly. 18+",
    }


# ── Two-Legged Tie ──────────────────────────────────────────────────────────

class TwoLegRequest(BaseModel):
    home_team: str
    home_strength: float = 0.75
    home_league: str = "premier-league"
    away_team: str
    away_strength: float = 0.75
    away_league: str = "la-liga"
    first_leg_home_score: int | None = None
    first_leg_away_score: int | None = None


@router.post("/two-leg-prediction")
async def two_leg_prediction(req: TwoLegRequest):
    """Predict qualification probability for a two-legged knockout tie."""
    result = predict_two_leg_tie(
        req.home_team, req.home_strength, req.home_league,
        req.away_team, req.away_strength, req.away_league,
        req.first_leg_home_score, req.first_leg_away_score,
    )
    return {
        "home_team": result.home_team,
        "away_team": result.away_team,
        "home_qualify_probability": result.home_qualify_probability,
        "away_qualify_probability": result.away_qualify_probability,
        "extra_time_probability": result.extra_time_probability,
        "penalty_probability": result.penalty_probability,
        "first_leg_played": result.first_leg_played,
        "aggregate_home": result.aggregate_home,
        "aggregate_away": result.aggregate_away,
        "narrative": result.narrative,
        "disclaimer": "Predictions are not guaranteed. Bet responsibly. 18+",
    }
