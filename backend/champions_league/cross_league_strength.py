"""
Cross-League Strength Model — Milestone 7
Converts domestic stats into a UEFA-adjusted strength rating so teams
from different leagues can be compared directly.

Uses publicly available UEFA league coefficients (no API key needed).
"""
from __future__ import annotations

# UEFA 5-year league coefficients (approximate, 2024/25 season)
# Source: public UEFA rankings
UEFA_LEAGUE_COEFFICIENTS: dict[str, float] = {
    "premier-league":   104.0,
    "la-liga":           91.0,
    "bundesliga":        79.0,
    "serie-a":           74.0,
    "ligue-1":           52.0,
    "eredivisie":        37.0,
    "primeira-liga":     42.0,
    "champions-league":  100.0,  # benchmark
}

# Normalised league multipliers (relative to an average of 70)
_AVG_COEFFICIENT = 70.0

def league_multiplier(league_slug: str) -> float:
    """Return a multiplier > 1 for strong leagues, < 1 for weaker ones."""
    coeff = UEFA_LEAGUE_COEFFICIENTS.get(league_slug, _AVG_COEFFICIENT)
    return round(coeff / _AVG_COEFFICIENT, 3)


# European experience bonus — teams with strong CL history perform better
# in European pressure situations
CL_EXPERIENCE_BONUS: dict[str, float] = {
    "Real Madrid":       0.15,
    "Bayern Munich":     0.12,
    "Barcelona":         0.12,
    "Manchester City":   0.10,
    "Liverpool":         0.10,
    "Chelsea":           0.08,
    "Juventus":          0.08,
    "PSG":               0.07,
    "Arsenal":           0.05,
    "Atletico Madrid":   0.09,
    "Borussia Dortmund": 0.07,
    "Inter Milan":       0.08,
    "AC Milan":          0.07,
    "Benfica":           0.06,
    "Porto":             0.06,
    "Ajax":              0.05,
}

def cl_experience_bonus(team_name: str) -> float:
    """Return a bonus [0–0.15] for teams with strong CL experience."""
    for key, bonus in CL_EXPERIENCE_BONUS.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return bonus
    return 0.02  # small default for any CL-qualified team


def adjusted_team_strength(
    domestic_strength: float,
    league_slug: str,
    team_name: str,
    is_home: bool = True,
) -> float:
    """
    Convert a domestic 0–1 strength score into a CL-adjusted rating.
    domestic_strength: output from outcome_model TeamMetrics (composite score)
    Returns a value roughly in range 0.3–1.2.
    """
    mult = league_multiplier(league_slug)
    exp_bonus = cl_experience_bonus(team_name)

    # Home advantage is smaller in neutral/away CL venues
    home_bonus = 0.03 if is_home else 0.0

    adjusted = domestic_strength * mult + exp_bonus + home_bonus
    return round(max(0.1, min(1.5, adjusted)), 3)


def compare_teams(
    home_team: str,
    home_strength: float,
    home_league: str,
    away_team: str,
    away_strength: float,
    away_league: str,
) -> dict:
    """
    Return a cross-league comparison dict with win probabilities.
    """
    h_adj = adjusted_team_strength(home_strength, home_league, home_team, is_home=True)
    a_adj = adjusted_team_strength(away_strength, away_league, away_team, is_home=False)

    total = h_adj + a_adj
    if total == 0:
        return {"home_win": 0.34, "draw": 0.32, "away_win": 0.34}

    h_raw = h_adj / total
    a_raw = a_adj / total
    closeness = 1 - abs(h_raw - a_raw)
    draw_p  = round(0.08 + closeness * 0.18, 3)   # 8–26% draw range in CL (less common)
    home_p  = round((h_raw * (1 - draw_p)), 3)
    away_p  = round(max(0.05, 1 - home_p - draw_p), 3)

    total_p = home_p + draw_p + away_p
    return {
        "home_adjusted_strength": h_adj,
        "away_adjusted_strength": a_adj,
        "home_win": round(home_p / total_p, 3),
        "draw":     round(draw_p / total_p, 3),
        "away_win": round(away_p / total_p, 3),
    }
