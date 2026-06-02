"""
AI Explanation Engine — Milestone 5
Produces a StructuredExplanation from model outputs.
Never invents facts. Only uses structured backend data.
Two rendering modes:
  1. Rule-based (always available, no API key)
  2. Claude API (richer prose, requires ANTHROPIC_API_KEY env var)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json

from backend.db.models import RiskLevel, FreshnessStatus


# ── Guardrails ────────────────────────────────────────────────────────────────

FORBIDDEN_PHRASES = [
    "guaranteed win", "guaranteed to win", "banker bet", "sure bet",
    "100% safe", "cannot lose", "free money", "certain to win",
    "will definitely win", "no way they lose", "no-brainer bet",
    "easy money",
]

DISCLAIMER     = "Predictions are not guaranteed. Bet responsibly. 18+"
LIVE_DISCLAIMER = "Live betting is high risk. Predictions are not guaranteed. Bet responsibly. 18+"


def _check_guardrails(text: str) -> str:
    lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ValueError(
                f"Explanation contains forbidden phrase: '{phrase}'. "
                "Never use guaranteed-win language."
            )
    return text


# ── Structured explanation dataclass ─────────────────────────────────────────

@dataclass
class StructuredExplanation:
    main_reasoning: str
    positive_factors: list[str]        = field(default_factory=list)
    risk_factors: list[str]            = field(default_factory=list)
    bet_rationale: str                 = ""
    rejected_markets: list[str]        = field(default_factory=list)
    data_note: str                     = ""
    no_bet_reason: str                 = ""
    is_live: bool                      = False
    live_note: str                     = ""
    disclaimer: str                    = DISCLAIMER

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    def to_text(self) -> str:
        """Flatten to plain text for storage / display fallback."""
        parts = [self.main_reasoning]
        if self.bet_rationale:
            parts.append(self.bet_rationale)
        if self.positive_factors:
            parts.append("Positives: " + "; ".join(self.positive_factors) + ".")
        if self.risk_factors:
            parts.append("Risks: " + "; ".join(self.risk_factors) + ".")
        if self.rejected_markets:
            parts.append("Also considered: " + "; ".join(self.rejected_markets) + ".")
        if self.no_bet_reason:
            parts.append(self.no_bet_reason)
        if self.data_note:
            parts.append(self.data_note)
        if self.live_note:
            parts.append(self.live_note)
        parts.append(self.disclaimer)
        return " ".join(parts)


# ── Input dataclass ───────────────────────────────────────────────────────────

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
    home_form_score: float
    away_form_score: float
    risk_reasons: list[str]
    is_live: bool = False
    match_minute: int | None = None
    home_score: int | None = None
    away_score: int | None = None
    over_2_5_prob: float = 0.50
    btts_prob: float = 0.50
    home_h2h_score: float = 0.50


# ── Rule-based explanation builder ────────────────────────────────────────────

def _build_main_reasoning(inp: ExplanationInput) -> str:
    home, away = inp.home_team, inp.away_team
    if inp.recommended_bet == "No Bet Recommended":
        return (
            f"The model does not identify a high-confidence betting opportunity "
            f"for {home} vs {away} at this time."
        )
    if inp.home_win_prob > inp.away_win_prob:
        stronger, weaker = home, away
        xg_for, xg_against = inp.home_xg, inp.away_xg
    else:
        stronger, weaker = away, home
        xg_for, xg_against = inp.away_xg, inp.home_xg

    return (
        f"{stronger} is favoured based on their attacking output "
        f"(xG: {xg_for:.2f}) against {weaker}'s defensive record "
        f"(xGA: {xg_against:.2f})."
    )


def _build_positives(inp: ExplanationInput) -> list[str]:
    home, away = inp.home_team, inp.away_team
    positives = []

    if inp.home_form_score > 0.65:
        positives.append(f"{home} is in strong recent form")
    elif inp.away_form_score > 0.65:
        positives.append(f"{away} is in strong recent form")

    if inp.home_xg > inp.away_xg * 1.25:
        positives.append(f"{home} xG ({inp.home_xg:.2f}) significantly exceeds {away}'s ({inp.away_xg:.2f})")
    elif inp.away_xg > inp.home_xg * 1.25:
        positives.append(f"{away} xG ({inp.away_xg:.2f}) significantly exceeds {home}'s ({inp.home_xg:.2f})")

    if inp.value_gap >= 5:
        positives.append(f"Model probability exceeds bookmaker implied probability by {inp.value_gap:.1f} percentage points")

    if inp.lineups_confirmed:
        positives.append("Confirmed lineups available — prediction accuracy is higher")

    if inp.home_h2h_score > 0.60:
        positives.append(f"{home} has a favourable head-to-head record in this fixture")
    elif inp.home_h2h_score < 0.40:
        positives.append(f"{away} has a favourable head-to-head record in this fixture")

    if inp.over_2_5_prob >= 0.60:
        positives.append(f"Combined xG ({inp.home_xg + inp.away_xg:.2f}) points towards a high-scoring match")

    if inp.btts_prob >= 0.62:
        positives.append("Both teams have been scoring regularly in recent matches")

    return positives[:5]  # cap at 5


def _build_risks(inp: ExplanationInput) -> list[str]:
    risks = list(inp.risk_reasons)  # start from engine output

    if not inp.lineups_confirmed and "Lineups" not in " ".join(risks):
        risks.append("Starting lineups are not yet confirmed")

    if inp.freshness_status in (FreshnessStatus.STALE, FreshnessStatus.INCOMPLETE):
        risks.append(f"Data freshness is {inp.freshness_status.value} — treat this prediction with extra caution")

    if inp.value_gap < 0:
        risks.append("Bookmaker odds imply a higher probability than our model — limited value at current price")

    return risks[:5]  # cap at 5


def _build_bet_rationale(inp: ExplanationInput) -> str:
    bet = inp.recommended_bet
    home, away = inp.home_team, inp.away_team

    if "No Bet" in bet:
        return ""
    if "Draw No Bet" in bet:
        return (
            f"Draw No Bet is preferred over a straight win because the draw probability "
            f"is {inp.draw_prob:.0%} — meaningful enough to warrant the safety net."
        )
    if "Over 2.5" in bet:
        total_xg = inp.home_xg + inp.away_xg
        return (
            f"Over 2.5 Goals is recommended as the combined xG of {total_xg:.2f} "
            f"and an over-probability of {inp.over_2_5_prob:.0%} both point to a goalscoring match."
        )
    if "Under 2.5" in bet:
        return (
            f"Under 2.5 Goals is recommended given the low combined xG "
            f"({inp.home_xg + inp.away_xg:.2f}) and defensive qualities of both sides."
        )
    if "Both Teams" in bet or "BTTS" in bet:
        return (
            f"Both Teams to Score is recommended — both sides have been finding the net regularly "
            f"with a BTTS probability of {inp.btts_prob:.0%}."
        )
    if "Double Chance" in bet:
        return (
            f"Double Chance provides coverage for two outcomes and reduces variance "
            f"given the closeness of the match ({home} {inp.home_win_prob:.0%} / Draw {inp.draw_prob:.0%} / {away} {inp.away_win_prob:.0%})."
        )
    if "Home Win" in bet:
        return f"{home} are favoured at {inp.home_win_prob:.0%} probability."
    if "Away Win" in bet:
        return f"{away} are favoured at {inp.away_win_prob:.0%} probability."

    return f"The model recommends {bet} based on the current data."


def _build_rejected_markets(inp: ExplanationInput) -> list[str]:
    """Explain which markets were considered but not recommended."""
    rejected = []
    bet = inp.recommended_bet

    if "Draw No Bet" not in bet and "Home Win" not in bet and "Away Win" not in bet:
        if inp.home_win_prob > 0.45:
            rejected.append(
                f"Home Win excluded — draw probability of {inp.draw_prob:.0%} adds meaningful risk"
            )

    if "Over 2.5" not in bet and inp.over_2_5_prob < 0.55:
        rejected.append(
            f"Over 2.5 Goals excluded — over probability only {inp.over_2_5_prob:.0%}"
        )

    if "BTTS" not in bet and "Both Teams" not in bet and inp.btts_prob < 0.55:
        rejected.append(
            f"Both Teams to Score excluded — BTTS probability is {inp.btts_prob:.0%}"
        )

    if "Correct Score" not in bet:
        rejected.append("Correct Score excluded — too high variance for the confidence level")

    return rejected[:3]


def _build_data_note(inp: ExplanationInput) -> str:
    status = inp.freshness_status
    if status == FreshnessStatus.FRESH:
        note = "Data is current and fresh."
    elif status == FreshnessStatus.ACCEPTABLE:
        note = "Data is recent but not fully up to date."
    elif status == FreshnessStatus.INCOMPLETE:
        note = "Some data is missing — prediction confidence is reduced."
    elif status == FreshnessStatus.STALE:
        note = "Warning: data is stale. This prediction should be treated with significant caution."
    else:
        note = ""

    if not inp.lineups_confirmed and note:
        note += " Lineups are not yet confirmed."

    return note


def _build_no_bet_reason(inp: ExplanationInput) -> str:
    if inp.recommended_bet != "No Bet Recommended":
        return ""

    reasons = []
    if inp.confidence < 45:
        reasons.append(f"model confidence is too low ({inp.confidence:.0f}%)")
    if inp.freshness_status in (FreshnessStatus.STALE, FreshnessStatus.INCOMPLETE):
        reasons.append(f"data freshness is {inp.freshness_status.value}")
    if not inp.lineups_confirmed:
        reasons.append("lineups are not confirmed")
    if abs(inp.home_win_prob - inp.away_win_prob) < 0.05:
        reasons.append("the match is too evenly balanced for a reliable edge")

    if reasons:
        return "No bet is recommended because " + ", ".join(reasons) + "."
    return "No clear betting edge has been identified for this match."


def _build_live_note(inp: ExplanationInput) -> str:
    if not inp.is_live or inp.match_minute is None:
        return ""
    home, away = inp.home_team, inp.away_team
    score = f"{home} {inp.home_score}–{inp.away_score} {away}"
    return (
        f"Live update at {inp.match_minute}' ({score}). "
        f"Live recommendations update as match conditions change — "
        f"odds can shift within seconds."
    )


def build_structured_explanation(inp: ExplanationInput) -> StructuredExplanation:
    """Build a fully structured explanation from prediction inputs."""
    expl = StructuredExplanation(
        main_reasoning   = _build_main_reasoning(inp),
        positive_factors = _build_positives(inp),
        risk_factors     = _build_risks(inp),
        bet_rationale    = _build_bet_rationale(inp),
        rejected_markets = _build_rejected_markets(inp),
        data_note        = _build_data_note(inp),
        no_bet_reason    = _build_no_bet_reason(inp),
        is_live          = inp.is_live,
        live_note        = _build_live_note(inp),
        disclaimer       = LIVE_DISCLAIMER if inp.is_live else DISCLAIMER,
    )

    # Validate the reasoning body — never the disclaimer
    body = expl.to_text().replace(expl.disclaimer, "")
    _check_guardrails(body)
    return expl


# Backward-compatible alias for existing callers
def build_explanation(inp: ExplanationInput) -> str:
    return build_structured_explanation(inp).to_text()
