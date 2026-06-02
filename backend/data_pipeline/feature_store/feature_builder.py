"""
Feature Builder
Converts raw DB data + scraped stats into normalised TeamMetrics
for the outcome model. All inputs are derived from free data sources.
"""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from backend.db.models import Match, Team, MatchStatus
from backend.data_pipeline.ingestion.football_data_co_uk import (
    fetch_league_results, compute_team_form, compute_home_away_form,
)
from backend.data_pipeline.ingestion.understat_scraper import get_team_xg_stats
from backend.prediction_engine.models.outcome_model import TeamMetrics


def _normalise(value: float, min_val: float, max_val: float) -> float:
    """Scale value to 0–1 range."""
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


async def get_days_since_last_match(
    db: AsyncSession, team_id: int, before: datetime
) -> int:
    """How many days since the team last played (fixture congestion proxy)."""
    result = await db.execute(
        select(Match)
        .where(
            and_(
                (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
                Match.kickoff_time < before,
                Match.status == MatchStatus.FINISHED,
            )
        )
        .order_by(Match.kickoff_time.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    if not last:
        return 7  # assume well-rested if no data
    delta = before - last.kickoff_time
    return max(1, delta.days)


async def build_team_metrics(
    db: AsyncSession,
    team: Team,
    league_slug: str,
    match_kickoff: datetime,
    is_home: bool,
) -> TeamMetrics:
    """
    Build normalised TeamMetrics for the outcome model.
    Uses football-data.co.uk for form + understat for xG.
    """
    # ── Form from football-data.co.uk ──────────────────────────────────
    try:
        hist_df = fetch_league_results(league_slug)
        form = compute_team_form(hist_df, team.name, last_n=5)
        home_away = compute_home_away_form(hist_df, team.name, last_n=5)
    except Exception:
        form = {}
        home_away = {"home": {}, "away": {}}

    win_rate = form.get("win_rate", 0.4)
    goals_scored = form.get("goals_scored", 1.2)
    goals_conceded = form.get("goals_conceded", 1.2)

    side_form = home_away["home"] if is_home else home_away["away"]
    side_win_rate = side_form.get("win_rate", 0.4)
    side_goals_scored = side_form.get("goals_scored", 1.2)

    # ── xG from Understat ───────────────────────────────────────────────
    try:
        xg_stats = get_team_xg_stats(league_slug, team.name)
    except Exception:
        xg_stats = {}

    xg_for  = xg_stats.get("xg_for_avg", goals_scored * 0.85)
    xg_against = xg_stats.get("xg_against_avg", goals_conceded * 0.85)

    # ── Fixture congestion ──────────────────────────────────────────────
    days_rest = await get_days_since_last_match(db, team.id, match_kickoff)
    congestion_score = _normalise(days_rest, 1, 10)  # 1 day = 0, 10+ days = 1

    # ── Normalise all metrics to 0–1 ───────────────────────────────────
    return TeamMetrics(
        recent_form_score    = _normalise(win_rate, 0, 1),
        home_away_score      = _normalise(side_win_rate, 0, 1),
        xg_score             = _normalise(xg_for, 0.3, 2.5),
        attacking_score      = _normalise(side_goals_scored, 0.3, 3.0),
        defensive_score      = _normalise(1 / max(0.1, xg_against), 0.3, 3.0),
        availability_score   = 0.85,   # placeholder — will be updated when lineup data arrives
        fixture_congestion_score = congestion_score,
        h2h_score            = 0.5,    # placeholder — h2h module comes in Milestone 7
    )


async def build_xg_estimates(
    league_slug: str,
    home_team_name: str,
    away_team_name: str,
) -> tuple[float, float]:
    """
    Return (home_xg, away_xg) estimates for a match.
    Uses Understat team averages + a simple Dixon-Coles-style adjustment.
    """
    try:
        home_stats = get_team_xg_stats(league_slug, home_team_name)
        away_stats = get_team_xg_stats(league_slug, away_team_name)
    except Exception:
        return 1.4, 1.1  # league average fallback

    home_xg_for     = home_stats.get("xg_for_home", 1.4)
    home_xg_against = home_stats.get("xg_against_home", 1.1)
    away_xg_for     = away_stats.get("xg_for_away", 1.1)
    away_xg_against = away_stats.get("xg_against_away", 1.3)

    # Geometric mean of attack strength vs opponent defence
    home_xg = round((home_xg_for + away_xg_against) / 2, 2)
    away_xg = round((away_xg_for + home_xg_against) / 2, 2)

    # Home advantage boost
    home_xg = round(home_xg * 1.10, 2)

    return max(0.3, home_xg), max(0.2, away_xg)
