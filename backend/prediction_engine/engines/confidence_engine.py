"""
Confidence Engine
Confidence is NOT just probability — it is penalised by data quality.
"""
from dataclasses import dataclass
from backend.db.models import FreshnessStatus


@dataclass
class ConfidenceInput:
    raw_model_probability: float    # 0–100, the model's raw win probability
    freshness_status: FreshnessStatus
    lineups_confirmed: bool
    odds_moving_heavily: bool       # True if odds shifted >15% since opening
    model_edge: float               # model_prob - implied_prob (percentage points)
    league_accuracy: float          # historical accuracy for this league (0–1)


def compute_confidence(inp: ConfidenceInput) -> dict:
    base = inp.raw_model_probability

    penalties = {}

    # Data freshness penalty
    if inp.freshness_status == FreshnessStatus.STALE:
        penalties["data_freshness"] = -15
    elif inp.freshness_status == FreshnessStatus.INCOMPLETE:
        penalties["data_freshness"] = -10
    elif inp.freshness_status == FreshnessStatus.ACCEPTABLE:
        penalties["data_freshness"] = -3
    else:
        penalties["data_freshness"] = 0

    # Lineup certainty
    penalties["lineup_uncertainty"] = 0 if inp.lineups_confirmed else -5

    # Market volatility
    penalties["market_volatility"] = -6 if inp.odds_moving_heavily else 0

    # Model edge bonus/penalty
    if inp.model_edge < 0:
        penalties["model_edge"] = -5
    elif inp.model_edge >= 10:
        penalties["model_edge"] = 3
    else:
        penalties["model_edge"] = 0

    # League accuracy adjustment
    league_adj = round((inp.league_accuracy - 0.5) * 10, 1)
    penalties["league_accuracy"] = league_adj

    total_penalty = sum(penalties.values())
    final = round(max(5.0, min(95.0, base + total_penalty)), 1)

    return {
        "raw_model_confidence": base,
        "penalties": penalties,
        "total_penalty": total_penalty,
        "final_confidence": final,
    }
