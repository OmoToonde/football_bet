"""
AI Explanation Engine
Translates model outputs into plain English using only structured backend data.
Never invents facts. Never uses guaranteed-win language.
"""
from dataclasses import dataclass
from backend.db.models import RiskLevel, FreshnessStatus


# Forbidden in the model reasoning body — guaranteed-WIN language only.
# "not guaranteed" is allowed (it's the disclaimer). We check the body before appending disclaimers.
FORBIDDEN_PHRASES = [
    "guaranteed win", "guaranteed to win", "banker bet", "sure bet",
    "100% safe", "cannot lose", "free money", "certain to win",
    "will definitely win", "no way they lose",
]

DISCLAIMER = "Predictions are not guaranteed. Bet responsibly."
LIVE_DISCLAIMER = "Live betting is high risk. Predictions are not guaranteed. Bet responsibly."


@dataclass
class ExplanationInput:
    home_team: str
    away_team: str
    recommended_bet: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    home_xg: float
    away_xg: float
    confidence: float
    risk_level: RiskLevel
    value_gap: float
    freshness_status: FreshnessStatus
    lineups_confirmed: bool
    home_form_score: float      # 0–1
    away_form_score: float      # 0–1
    risk_reasons: list[str]
    is_live: bool = False
    match_minute: int | None = None
    home_score: int | None = None
    away_score: int | None = None


def _validate(text: str) -> str:
    lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ValueError(
                f"Explanation contains forbidden phrase: '{phrase}'. "
                "Never use guaranteed-win language."
            )
    return text


def build_explanation(inp: ExplanationInput) -> str:
    home, away = inp.home_team, inp.away_team
    lines: list[str] = []

    # Opening line
    if inp.home_win_prob > inp.away_win_prob:
        stronger, weaker = home, away
        xg_for, xg_against = inp.home_xg, inp.away_xg
    else:
        stronger, weaker = away, home
        xg_for, xg_against = inp.away_xg, inp.home_xg

    lines.append(
        f"{stronger} is favoured based on their attacking output "
        f"(xG: {xg_for:.2f}) compared to {weaker}'s defensive record "
        f"(xGA: {xg_against:.2f})."
    )

    # Recommended bet reasoning
    bet = inp.recommended_bet
    if bet == "No Bet Recommended":
        lines.append("The model does not find a high-confidence opportunity for this match.")
    elif "Draw No Bet" in bet:
        lines.append(
            f"Draw No Bet is recommended because the draw probability is still meaningful "
            f"({inp.draw_prob:.0%}), reducing the risk of a straight win bet."
        )
    elif "over_2_5" in bet.lower() or "over 2.5" in bet.lower():
        lines.append(
            f"Over 2.5 goals is recommended as both teams have combined xG of "
            f"{inp.home_xg + inp.away_xg:.2f}, suggesting an open game."
        )
    else:
        lines.append(f"The recommended bet is {bet}.")

    # Positives
    positives: list[str] = []
    if inp.home_form_score > 0.65:
        positives.append(f"{home} is in strong recent form")
    if inp.home_xg > inp.away_xg * 1.3:
        positives.append(f"{home} xG is significantly higher than {away}'s")
    if inp.value_gap >= 5:
        positives.append(f"The odds offer {inp.value_gap:.1f}pp value over the model probability")
    if inp.lineups_confirmed:
        positives.append("Lineups are confirmed")

    if positives:
        lines.append("Positives: " + "; ".join(positives) + ".")

    # Risks
    if inp.risk_reasons:
        lines.append("Risks: " + "; ".join(inp.risk_reasons) + ".")

    # Freshness note
    if inp.freshness_status in (FreshnessStatus.STALE, FreshnessStatus.INCOMPLETE):
        lines.append(
            f"Warning: data freshness is {inp.freshness_status.value}. "
            "This prediction should be treated with extra caution."
        )

    # Live mode note
    if inp.is_live and inp.match_minute is not None:
        lines.append(
            f"Live update at minute {inp.match_minute} "
            f"(score: {home} {inp.home_score}–{inp.away_score} {away}). "
            "Live conditions can change rapidly."
        )

    disclaimer = LIVE_DISCLAIMER if inp.is_live else DISCLAIMER
    lines.append(disclaimer)

    # Validate the reasoning body BEFORE appending the disclaimer
    body = " ".join(lines[:-1])  # all but the final disclaimer line
    _validate(body)
    return " ".join(lines)
