"""
Risk Engine — separate from confidence.
A correct-score bet can have decent confidence but still be High risk.
"""
from dataclasses import dataclass
from backend.db.models import RiskLevel


@dataclass
class RiskInput:
    bet_type: str               # e.g. "home_win", "correct_score", "over_2_5"
    draw_probability: float     # 0–1
    confidence: float           # 0–100
    lineups_confirmed: bool
    odds_moving_heavily: bool
    is_live: bool
    away_scoring_rate: float    # fraction of recent games away team scored in


BET_TYPE_BASE_RISK = {
    "correct_score":   RiskLevel.HIGH,
    "first_goalscorer": RiskLevel.HIGH,
    "home_win":        RiskLevel.MEDIUM,
    "away_win":        RiskLevel.MEDIUM,
    "draw":            RiskLevel.HIGH,
    "draw_no_bet":     RiskLevel.LOW,
    "double_chance":   RiskLevel.LOW,
    "over_2_5":        RiskLevel.MEDIUM,
    "under_2_5":       RiskLevel.MEDIUM,
    "btts":            RiskLevel.MEDIUM,
    "no_bet":          RiskLevel.NO_BET,
}

_RISK_ORDER = [
    RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH,
    RiskLevel.VERY_HIGH, RiskLevel.LIVE_HIGH_RISK, RiskLevel.NO_BET,
]


def _escalate(level: RiskLevel, steps: int = 1) -> RiskLevel:
    idx = _RISK_ORDER.index(level)
    return _RISK_ORDER[min(idx + steps, len(_RISK_ORDER) - 2)]


def compute_risk(inp: RiskInput) -> dict:
    if inp.bet_type == "no_bet":
        return {"risk_level": RiskLevel.NO_BET, "risk_reasons": ["No bet recommended by model"]}

    risk = BET_TYPE_BASE_RISK.get(inp.bet_type, RiskLevel.MEDIUM)
    reasons: list[str] = []

    if inp.draw_probability >= 0.25:
        risk = _escalate(risk)
        reasons.append(f"Draw probability is {inp.draw_probability:.0%}")

    if not inp.lineups_confirmed:
        risk = _escalate(risk)
        reasons.append("Lineups are not confirmed yet")

    if inp.odds_moving_heavily:
        risk = _escalate(risk)
        reasons.append("Odds are moving significantly")

    if inp.confidence < 55:
        risk = _escalate(risk)
        reasons.append(f"Model confidence is low ({inp.confidence:.0f}%)")

    if inp.away_scoring_rate >= 0.8:
        reasons.append(f"Away team scored in {inp.away_scoring_rate:.0%} of recent matches")

    if inp.is_live:
        risk = RiskLevel.LIVE_HIGH_RISK
        reasons.insert(0, "Live in-play recommendation — odds can change in seconds")

    return {"risk_level": risk, "risk_reasons": reasons}
