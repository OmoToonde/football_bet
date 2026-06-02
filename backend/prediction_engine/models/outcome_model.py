"""
Match Outcome Model — weighted scoring model for MVP.
Produces home_win, draw, away_win probabilities from team metrics.
"""
from dataclasses import dataclass
from backend.config import settings


@dataclass
class TeamMetrics:
    recent_form_score: float        # 0–1 normalised
    home_away_score: float          # 0–1 normalised
    xg_score: float                 # 0–1 normalised
    attacking_score: float          # 0–1 normalised
    defensive_score: float          # 0–1 normalised (higher = stronger defence)
    availability_score: float       # 0–1, 1 = full squad available
    fixture_congestion_score: float # 0–1, 1 = well rested
    h2h_score: float                # 0–1 normalised


@dataclass
class OutcomeModelInput:
    home: TeamMetrics
    away: TeamMetrics
    odds_movement_score: float  # +ve = home favoured by market, -ve = away


@dataclass
class OutcomeModelOutput:
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    home_strength: float
    away_strength: float


def _team_strength(m: TeamMetrics, odds_movement: float, side: str) -> float:
    """Compute weighted composite strength for one team."""
    w = settings
    direction = 1 if side == "home" else -1

    return (
        m.recent_form_score       * w.weight_recent_form +
        m.home_away_score         * w.weight_home_away +
        m.xg_score                * w.weight_xg +
        m.attacking_score         * w.weight_attacking +
        m.defensive_score         * w.weight_defensive +
        m.availability_score      * w.weight_player_availability +
        m.fixture_congestion_score * w.weight_fixture_congestion +
        m.h2h_score               * w.weight_h2h +
        (odds_movement * direction) * w.weight_odds_movement
    )


def predict_outcome(inp: OutcomeModelInput) -> OutcomeModelOutput:
    home_str = _team_strength(inp.home, inp.odds_movement_score, "home")
    away_str = _team_strength(inp.away, inp.odds_movement_score, "away")

    total = home_str + away_str
    if total == 0:
        return OutcomeModelOutput(0.34, 0.33, 0.33, 0.5, 0.5)

    # Raw split weighted by relative strength
    home_raw = home_str / total
    away_raw = away_str / total

    # Draw probability increases the closer the teams are in strength
    closeness = 1 - abs(home_raw - away_raw)
    draw_prob = round(0.10 + closeness * 0.20, 3)  # 10–30% draw range

    home_prob = round((home_raw * (1 - draw_prob)), 3)
    away_prob = round(1 - home_prob - draw_prob, 3)

    # Clamp to valid probabilities
    home_prob = max(0.05, min(0.85, home_prob))
    away_prob = max(0.05, min(0.85, away_prob))
    draw_prob = max(0.05, min(0.40, draw_prob))

    # Re-normalise to sum to 1
    total_prob = home_prob + draw_prob + away_prob
    return OutcomeModelOutput(
        home_win_probability=round(home_prob / total_prob, 3),
        draw_probability=round(draw_prob / total_prob, 3),
        away_win_probability=round(away_prob / total_prob, 3),
        home_strength=round(home_str, 3),
        away_strength=round(away_str, 3),
    )
