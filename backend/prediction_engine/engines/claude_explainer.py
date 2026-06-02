"""
Claude API Explanation Renderer — Milestone 5
Takes a StructuredExplanation and uses Claude to produce richer natural-language prose.
Completely optional — if ANTHROPIC_API_KEY is not set, returns the rule-based text as-is.
Falls back silently; the product works without it.
"""
from __future__ import annotations
import os
import logging

from backend.prediction_engine.engines.explanation_engine import (
    StructuredExplanation, FORBIDDEN_PHRASES, DISCLAIMER, LIVE_DISCLAIMER,
)

logger = logging.getLogger(__name__)

_CLIENT = None


def _get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        _CLIENT = anthropic.Anthropic(api_key=api_key)
        return _CLIENT
    except ImportError:
        logger.warning("anthropic package not installed — rule-based explanations only")
        return None


_SYSTEM_PROMPT = """You are the explanation engine for an AI football betting intelligence app.
Your job is to convert structured prediction data into clear, honest, plain-English analysis.

Rules you MUST follow:
- Never invent facts. Only use the data provided.
- Never use guaranteed-win language: no "guaranteed", "banker", "sure bet", "cannot lose", "certain to win", "free money", "no-brainer".
- Never use urgent language: no "act now", "do not miss", "last chance".
- Always be honest about uncertainty and risk.
- Write in a calm, analytical, professional tone — like a football analyst, not a tipster.
- Keep the explanation under 120 words.
- End with exactly this disclaimer (do not modify it): {disclaimer}
""".strip()

_USER_TEMPLATE = """
Match: {home_team} vs {away_team}
Recommended bet: {recommended_bet}
Confidence: {confidence:.0f}%
Risk level: {risk_level}

Main reasoning: {main_reasoning}
Positive factors: {positives}
Risk factors: {risks}
Bet rationale: {bet_rationale}
Markets considered and rejected: {rejected}
Data note: {data_note}
{no_bet_section}
{live_section}

Write the explanation now (under 120 words, end with the disclaimer):
""".strip()


def render_with_claude(
    expl: StructuredExplanation,
    home_team: str,
    away_team: str,
    recommended_bet: str,
    confidence: float,
    risk_level: str,
) -> str:
    """
    Use Claude to render a richer explanation from structured data.
    Returns rule-based text if Claude is unavailable or fails.
    """
    client = _get_client()
    if not client:
        return expl.to_text()

    disclaimer = LIVE_DISCLAIMER if expl.is_live else DISCLAIMER
    system = _SYSTEM_PROMPT.format(disclaimer=disclaimer)

    user_msg = _USER_TEMPLATE.format(
        home_team       = home_team,
        away_team       = away_team,
        recommended_bet = recommended_bet,
        confidence      = confidence,
        risk_level      = risk_level,
        main_reasoning  = expl.main_reasoning,
        positives       = "; ".join(expl.positive_factors) or "None identified",
        risks           = "; ".join(expl.risk_factors) or "None identified",
        bet_rationale   = expl.bet_rationale or "N/A",
        rejected        = "; ".join(expl.rejected_markets) or "N/A",
        data_note       = expl.data_note or "Data is fresh",
        no_bet_section  = f"No-bet reason: {expl.no_bet_reason}" if expl.no_bet_reason else "",
        live_section    = f"Live context: {expl.live_note}" if expl.live_note else "",
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # fast + cheap for explanation generation
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = response.content[0].text.strip()

        # Guardrail: never return if forbidden phrase slipped through
        lower = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lower:
                logger.warning(f"Claude output contained forbidden phrase '{phrase}' — using fallback")
                return expl.to_text()

        return text
    except Exception as e:
        logger.warning(f"Claude explanation failed ({e}) — using rule-based fallback")
        return expl.to_text()
