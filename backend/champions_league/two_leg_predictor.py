"""
Two-Legged Tie Predictor — Milestone 7
Models qualification probability across a home-and-away knockout tie,
accounting for aggregate score, away goals (legacy rule removed but
extra time + penalties still apply), squad depth under fatigue,
and tactical conservatism after a first-leg advantage.
"""
from __future__ import annotations
from dataclasses import dataclass
from scipy.stats import poisson
import numpy as np

from backend.champions_league.cross_league_strength import compare_teams


@dataclass
class TwoLegInput:
    home_team: str
    home_strength: float
    home_league: str
    away_team: str
    away_strength: float
    away_league: str
    # First-leg result (None = not yet played)
    first_leg_home_score: int | None = None
    first_leg_away_score: int | None = None
    # Penalty shootout strength estimate [0–1]
    home_penalty_strength: float = 0.5
    away_penalty_strength: float = 0.5


@dataclass
class TwoLegOutput:
    home_team: str
    away_team: str
    home_qualify_probability: float
    away_qualify_probability: float
    extra_time_probability: float
    penalty_probability: float
    first_leg_played: bool
    aggregate_home: int
    aggregate_away: int
    expected_second_leg: str | None  # e.g. "1-0"
    narrative: str


def _poisson_goals(xg: float, max_goals: int = 7) -> list[float]:
    return [poisson.pmf(g, xg) for g in range(max_goals + 1)]


def _xg_from_strength(attack: float, defence: float) -> float:
    """Rough xG estimate from relative strength ratings."""
    base = 1.35  # average CL match goals per team
    raw = base * (attack / max(0.1, defence))
    return round(max(0.2, min(4.0, raw)), 2)


def simulate_two_legs(inp: TwoLegInput, simulations: int = 50_000) -> TwoLegOutput:
    """
    Monte Carlo simulation of two-legged tie outcomes.
    Second leg: away team from first leg plays at home.
    """
    probs = compare_teams(
        inp.home_team, inp.home_strength, inp.home_league,
        inp.away_team, inp.away_strength, inp.away_league,
    )

    h_adj = probs["home_adjusted_strength"]
    a_adj = probs["away_adjusted_strength"]

    # First leg: home team plays at home
    leg1_h_xg = _xg_from_strength(h_adj, a_adj) * 1.08   # home advantage
    leg1_a_xg = _xg_from_strength(a_adj, h_adj)

    # Second leg: roles reverse — away team now at home
    leg2_h_xg = _xg_from_strength(a_adj, h_adj) * 1.08
    leg2_a_xg = _xg_from_strength(h_adj, a_adj)

    first_leg_played = (
        inp.first_leg_home_score is not None and
        inp.first_leg_away_score is not None
    )

    if first_leg_played:
        agg_h_after_leg1 = inp.first_leg_home_score
        agg_a_after_leg1 = inp.first_leg_away_score

        # Adjust second leg xG based on first leg deficit/lead
        deficit = agg_h_after_leg1 - agg_a_after_leg1
        # Team behind (away team) pushes harder in second leg
        if deficit > 0:
            leg2_h_xg *= (1.0 + 0.08 * deficit)
        elif deficit < 0:
            leg2_a_xg *= (1.0 + 0.08 * abs(deficit))

        expected_second_leg = f"{round(leg2_a_xg)}-{round(leg2_a_xg)}"
    else:
        agg_h_after_leg1 = 0
        agg_a_after_leg1 = 0
        expected_second_leg = f"{round(leg1_h_xg)}-{round(leg1_a_xg)}"

    # Run Monte Carlo
    rng = np.random.default_rng(42)
    home_qualifies = 0
    went_to_extra = 0
    went_to_pens = 0

    for _ in range(simulations):
        if not first_leg_played:
            l1_h = rng.poisson(leg1_h_xg)
            l1_a = rng.poisson(leg1_a_xg)
        else:
            l1_h = agg_h_after_leg1
            l1_a = agg_a_after_leg1

        # Second leg (played at away team's ground)
        l2_a = rng.poisson(leg2_h_xg)   # original away team at home
        l2_h = rng.poisson(leg2_a_xg)   # original home team away

        agg_h = l1_h + l2_h
        agg_a = l1_a + l2_a

        if agg_h > agg_a:
            home_qualifies += 1
        elif agg_a > agg_h:
            pass  # away qualifies
        else:
            # Tied on aggregate → extra time
            went_to_extra += 1
            et_h = rng.poisson(0.4)
            et_a = rng.poisson(0.4)
            if et_h > et_a:
                home_qualifies += 1
            elif et_a > et_h:
                pass
            else:
                # Penalties
                went_to_pens += 1
                ph = inp.home_penalty_strength
                pa = inp.away_penalty_strength
                # Normalise so one team wins the shootout
                if rng.random() < ph / (ph + pa):
                    home_qualifies += 1

    home_qual_prob = round(home_qualifies / simulations, 3)
    away_qual_prob = round(1 - home_qual_prob, 3)
    et_prob  = round(went_to_extra / simulations, 3)
    pen_prob = round(went_to_pens / simulations, 3)

    # Narrative
    if first_leg_played:
        agg = f"{agg_h_after_leg1}-{agg_a_after_leg1}"
        if agg_h_after_leg1 > agg_a_after_leg1:
            leader = inp.home_team
            trailer = inp.away_team
        elif agg_a_after_leg1 > agg_h_after_leg1:
            leader = inp.away_team
            trailer = inp.home_team
        else:
            leader = trailer = None

        if leader:
            narrative = (
                f"{leader} lead {agg} after the first leg. "
                f"{leader} qualify with {max(home_qual_prob if leader == inp.home_team else away_qual_prob, 0):.0%} probability. "
                f"The model gives {inp.home_team} {home_qual_prob:.0%} and "
                f"{inp.away_team} {away_qual_prob:.0%} chance of progressing."
            )
        else:
            narrative = (
                f"The first leg finished {agg} — the tie is level. "
                f"Extra time is needed in {et_prob:.0%} of simulations "
                f"and penalties in {pen_prob:.0%}."
            )
    else:
        narrative = (
            f"Pre-tie simulation: {inp.home_team} ({home_qual_prob:.0%}) vs "
            f"{inp.away_team} ({away_qual_prob:.0%}). "
            f"Extra time expected in {et_prob:.0%} of simulations."
        )

    return TwoLegOutput(
        home_team                = inp.home_team,
        away_team                = inp.away_team,
        home_qualify_probability = home_qual_prob,
        away_qualify_probability = away_qual_prob,
        extra_time_probability   = et_prob,
        penalty_probability      = pen_prob,
        first_leg_played         = first_leg_played,
        aggregate_home           = agg_h_after_leg1,
        aggregate_away           = agg_a_after_leg1,
        expected_second_leg      = expected_second_leg,
        narrative                = narrative,
    )
