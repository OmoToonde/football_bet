"""
Champions League Tournament Simulator — Milestone 7
Monte Carlo simulation of the full CL tournament.

2024/25 format: 36-team league phase (8 matches each)
  → Top 8 qualify directly for R16
  → Positions 9-24 play knockout playoffs
  → Bottom 12 eliminated
Then R16 → QF → SF → Final.

Uses UEFA-adjusted team strength ratings derived from domestic performance
and UEFA coefficients. No API key required.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from backend.champions_league.cross_league_strength import adjusted_team_strength


@dataclass
class CLTeam:
    name: str
    league: str
    domestic_strength: float   # 0–1, from outcome model or hardcoded rating
    cl_experience: float = 0.5 # 0–1, European familiarity
    seed: int = 1              # UCL seeding pot (1-4)


# 2025/26 CL teams — realistic participant list with strength ratings
# Ratings derived from UEFA coefficients + recent domestic performance
DEFAULT_CL_TEAMS: list[CLTeam] = [
    # Pot 1 (highest ranked)
    CLTeam("Real Madrid",       "la-liga",      0.92, 1.0, 1),
    CLTeam("Manchester City",   "premier-league", 0.90, 0.9, 1),
    CLTeam("Bayern Munich",     "bundesliga",   0.89, 0.9, 1),
    CLTeam("Paris Saint-Germain", "ligue-1",    0.88, 0.8, 1),
    CLTeam("Liverpool",         "premier-league", 0.87, 0.9, 1),
    CLTeam("Barcelona",         "la-liga",      0.86, 0.9, 1),
    CLTeam("Inter Milan",       "serie-a",      0.84, 0.8, 1),
    CLTeam("Atletico Madrid",   "la-liga",      0.83, 0.8, 1),
    # Pot 2
    CLTeam("Arsenal",           "premier-league", 0.82, 0.7, 2),
    CLTeam("Borussia Dortmund", "bundesliga",   0.80, 0.75, 2),
    CLTeam("Juventus",          "serie-a",      0.79, 0.8, 2),
    CLTeam("Chelsea",           "premier-league", 0.78, 0.75, 2),
    CLTeam("AC Milan",          "serie-a",      0.77, 0.75, 2),
    CLTeam("Bayer Leverkusen",  "bundesliga",   0.76, 0.6, 2),
    CLTeam("Benfica",           "primeira-liga", 0.74, 0.65, 2),
    CLTeam("Real Sociedad",     "la-liga",      0.72, 0.55, 2),
    # Pot 3
    CLTeam("Napoli",            "serie-a",      0.71, 0.6, 3),
    CLTeam("Porto",             "primeira-liga", 0.70, 0.65, 3),
    CLTeam("RB Leipzig",        "bundesliga",   0.69, 0.55, 3),
    CLTeam("Tottenham",         "premier-league", 0.68, 0.6, 3),
    CLTeam("Aston Villa",       "premier-league", 0.67, 0.45, 3),
    CLTeam("Ajax",              "eredivisie",   0.66, 0.7, 3),
    CLTeam("Shakhtar Donetsk",  "premier-league", 0.64, 0.55, 3),
    CLTeam("Club Brugge",       "premier-league", 0.62, 0.5, 3),
    # Pot 4 (lower seeds)
    CLTeam("Celtic",            "premier-league", 0.60, 0.5, 4),
    CLTeam("Feyenoord",         "eredivisie",   0.59, 0.5, 4),
    CLTeam("Sturm Graz",        "premier-league", 0.55, 0.35, 4),
    CLTeam("Slavia Prague",     "premier-league", 0.54, 0.4, 4),
    CLTeam("RB Salzburg",       "premier-league", 0.58, 0.45, 4),
    CLTeam("Girona",            "la-liga",      0.60, 0.3, 4),
    CLTeam("Sparta Prague",     "premier-league", 0.53, 0.35, 4),
    CLTeam("Young Boys",        "premier-league", 0.50, 0.3, 4),
    # Additional teams to reach 36
    CLTeam("Monaco",            "ligue-1",      0.65, 0.5, 3),
    CLTeam("Sporting CP",       "primeira-liga", 0.66, 0.55, 3),
    CLTeam("Lille",             "ligue-1",      0.64, 0.5, 4),
    CLTeam("Stuttgart",         "bundesliga",   0.65, 0.45, 4),
]


@dataclass
class SimulationResult:
    winner_probabilities: dict[str, float]        = field(default_factory=dict)
    final_probabilities: dict[str, float]          = field(default_factory=dict)
    semi_final_probabilities: dict[str, float]     = field(default_factory=dict)
    quarter_final_probabilities: dict[str, float]  = field(default_factory=dict)
    r16_probabilities: dict[str, float]            = field(default_factory=dict)
    league_phase_top8: dict[str, float]            = field(default_factory=dict)
    simulations_run: int = 0


def _match_result(team_a: CLTeam, team_b: CLTeam, rng: np.random.Generator, neutral: bool = False) -> CLTeam:
    """Simulate one match and return the winner."""
    strength_a = adjusted_team_strength(team_a.domestic_strength, team_a.league, team_a.name, is_home=not neutral)
    strength_b = adjusted_team_strength(team_b.domestic_strength, team_b.league, team_b.name, is_home=neutral)

    prob_a = strength_a / (strength_a + strength_b)
    return team_a if rng.random() < prob_a else team_b


def simulate_league_phase(teams: list[CLTeam], rng: np.random.Generator) -> list[CLTeam]:
    """
    Simplified league phase simulation.
    Each team plays 8 matches against randomly drawn opponents.
    Returns teams sorted by simulated points (top 24 qualify in some form).
    """
    points: dict[str, float] = {t.name: 0.0 for t in teams}
    team_map = {t.name: t for t in teams}

    # Each team plays 8 matches — simulate via random pairings
    for team in teams:
        opponents = rng.choice([t for t in teams if t.name != team.name], size=8, replace=False)
        for opp in opponents:
            winner = _match_result(team, opp, rng)
            points[winner.name] += 3
            if winner.name == team.name:
                pass  # already counted
            # Away draw probability
            if rng.random() < 0.20:  # 20% chance draw
                points[team.name] += 1
                points[opp.name] += 1

    sorted_teams = sorted(teams, key=lambda t: points[t.name], reverse=True)
    return sorted_teams


def _knockout_round(teams: list[CLTeam], rng: np.random.Generator) -> list[CLTeam]:
    """Simulate one knockout round (pairs of teams), returns winners."""
    winners = []
    for i in range(0, len(teams), 2):
        if i + 1 < len(teams):
            winners.append(_match_result(teams[i], teams[i + 1], rng, neutral=True))
        else:
            winners.append(teams[i])  # bye
    return winners


def run_tournament_simulation(
    teams: list[CLTeam] | None = None,
    simulations: int = 10_000,
) -> SimulationResult:
    """
    Full Monte Carlo tournament simulation.
    Returns probabilities of reaching each stage.
    """
    if teams is None:
        teams = DEFAULT_CL_TEAMS

    rng = np.random.default_rng(42)
    result = SimulationResult(simulations_run=simulations)

    counts: dict[str, dict[str, int]] = {
        "winner": defaultdict(int),
        "final": defaultdict(int),
        "semi": defaultdict(int),
        "quarter": defaultdict(int),
        "r16": defaultdict(int),
        "top8": defaultdict(int),
    }

    for _ in range(simulations):
        sim_teams = list(teams)
        rng.shuffle(sim_teams)

        # League phase
        standings = simulate_league_phase(sim_teams, rng)
        top_8   = standings[:8]
        next_16 = standings[8:24]   # playoff round

        for t in top_8:
            counts["top8"][t.name] += 1
            counts["r16"][t.name] += 1  # top 8 go straight to R16

        # Knockout playoffs (9–24): 16 teams → 8 through to R16
        rng.shuffle(next_16)
        playoff_winners = _knockout_round(next_16, rng)
        for t in playoff_winners:
            counts["r16"][t.name] += 1

        # Round of 16
        r16_field = top_8 + playoff_winners
        rng.shuffle(r16_field)
        qf_field = _knockout_round(r16_field, rng)
        for t in qf_field:
            counts["quarter"][t.name] += 1

        # Quarter-finals
        rng.shuffle(qf_field)
        sf_field = _knockout_round(qf_field, rng)
        for t in sf_field:
            counts["semi"][t.name] += 1

        # Semi-finals
        rng.shuffle(sf_field)
        final_field = _knockout_round(sf_field, rng)
        for t in final_field:
            counts["final"][t.name] += 1

        # Final
        if len(final_field) == 2:
            champion = _match_result(final_field[0], final_field[1], rng, neutral=True)
        else:
            champion = final_field[0]
        counts["winner"][champion.name] += 1

    def to_probs(counter: dict) -> dict[str, float]:
        return {k: round(v / simulations, 4) for k, v in
                sorted(counter.items(), key=lambda x: -x[1])}

    result.winner_probabilities        = to_probs(counts["winner"])
    result.final_probabilities         = to_probs(counts["final"])
    result.semi_final_probabilities    = to_probs(counts["semi"])
    result.quarter_final_probabilities = to_probs(counts["quarter"])
    result.r16_probabilities           = to_probs(counts["r16"])
    result.league_phase_top8           = to_probs(counts["top8"])

    return result
