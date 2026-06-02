"""
Expected Score / Correct Score Model
Uses Poisson distribution over expected goals to generate scoreline probabilities.
"""
from dataclasses import dataclass
from scipy.stats import poisson
import numpy as np


@dataclass
class ScoreModelInput:
    home_xg: float
    away_xg: float


@dataclass
class ScorelineProbability:
    home_goals: int
    away_goals: int
    probability: float


@dataclass
class ScoreModelOutput:
    home_xg: float
    away_xg: float
    most_likely_score: str          # e.g. "2-1"
    most_likely_probability: float
    top_scorelines: list[ScorelineProbability]
    over_2_5_probability: float
    btts_probability: float


def predict_scorelines(inp: ScoreModelInput, max_goals: int = 6) -> ScoreModelOutput:
    """
    Generate scoreline probabilities using independent Poisson distributions.
    home_xg and away_xg are the expected goals for each team.
    """
    home_probs = [poisson.pmf(g, inp.home_xg) for g in range(max_goals + 1)]
    away_probs = [poisson.pmf(g, inp.away_xg) for g in range(max_goals + 1)]

    scorelines: list[ScorelineProbability] = []
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = home_probs[h] * away_probs[a]
            scorelines.append(ScorelineProbability(h, a, round(prob, 4)))

    scorelines.sort(key=lambda x: x.probability, reverse=True)

    best = scorelines[0]
    most_likely_score = f"{best.home_goals}-{best.away_goals}"

    # Over 2.5 goals
    over_2_5 = sum(
        s.probability for s in scorelines
        if s.home_goals + s.away_goals > 2
    )

    # Both teams to score
    btts = sum(
        s.probability for s in scorelines
        if s.home_goals > 0 and s.away_goals > 0
    )

    return ScoreModelOutput(
        home_xg=inp.home_xg,
        away_xg=inp.away_xg,
        most_likely_score=most_likely_score,
        most_likely_probability=round(best.probability, 4),
        top_scorelines=scorelines[:8],
        over_2_5_probability=round(over_2_5, 4),
        btts_probability=round(btts, 4),
    )
