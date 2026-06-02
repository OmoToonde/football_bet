"""
Feature Builder
Converts raw DB data + scraped stats into normalised TeamMetrics
for the outcome model. All inputs are derived from free data sources.
Results are cached to avoid redundant network calls within the same run.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from backend.db.models import Match, Team, MatchStatus
from backend.data_pipeline.ingestion.football_data_co_uk import (
    fetch_league_results, compute_team_form, compute_home_away_form,
)
from backend.data_pipeline.ingestion.understat_scraper import get_team_xg_stats
from backend.data_pipeline.ingestion.h2h import get_h2h_record
from backend.data_pipeline.feature_store.cache import feature_cache
from backend.prediction_engine.models.outcome_model import TeamMetrics


def _normalise(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def _cached_league_df(league_slug: str):
    key = f"csv_{league_slug}"
    df = feature_cache.get(key)
    if df is None:
        df = fetch_league_results(league_slug)
        feature_cache.set(key, df)
    return df


def _cached_xg(league_slug: str, team_name: str) -> dict:
    key = f"xg_{league_slug}_{team_name}"
    stats = feature_cache.get(key)
    if stats is None:
        stats = get_team_xg_stats(league_slug, team_name)
        feature_cache.set(key, stats)
    return stats


async def get_days_since_last_match(
    db: AsyncSession, team_id: int, before: datetime
) -> int:
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
        return 7
    delta = before - last.kickoff_time
    return max(1, delta.days)


async def build_team_metrics(
    db: AsyncSession,
    team: Team,
    league_slug: str,
    match_kickoff: datetime,
    is_home: bool,
    opponent_name: str = "",
) -> TeamMetrics:
    """
    Build normalised TeamMetrics for the outcome model.
    Now uses cache + real H2H data.
    """
    # ── Form (cached CSV) ───────────────────────────────────────────────
    try:
        hist_df = _cached_league_df(league_slug)
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

    # ── xG (cached Understat) ───────────────────────────────────────────
    try:
        xg_stats = _cached_xg(league_slug, team.name)
    except Exception:
        xg_stats = {}

    xg_for     = xg_stats.get("xg_for_avg", goals_scored * 0.85)
    xg_against = xg_stats.get("xg_against_avg", goals_conceded * 0.85)

    # ── H2H ─────────────────────────────────────────────────────────────
    h2h_score = 0.5
    if opponent_name:
        try:
            h2h = get_h2h_record(league_slug, team.name if is_home else opponent_name,
                                 opponent_name if is_home else team.name)
            h2h_score = h2h["h2h_score"] if is_home else (1 - h2h["h2h_score"])
        except Exception:
            pass

    # ── Fixture congestion ──────────────────────────────────────────────
    days_rest = await get_days_since_last_match(db, team.id, match_kickoff)
    congestion_score = _normalise(days_rest, 1, 10)

    return TeamMetrics(
        recent_form_score        = _normalise(win_rate, 0, 1),
        home_away_score          = _normalise(side_win_rate, 0, 1),
        xg_score                 = _normalise(xg_for, 0.3, 2.5),
        attacking_score          = _normalise(side_goals_scored, 0.3, 3.0),
        defensive_score          = _normalise(1 / max(0.1, xg_against), 0.3, 3.0),
        availability_score       = 0.85,  # updated by lineup pipeline (Milestone 4+)
        fixture_congestion_score = congestion_score,
        h2h_score                = h2h_score,
    )


async def build_xg_estimates(
    league_slug: str,
    home_team_name: str,
    away_team_name: str,
) -> tuple[float, float]:
    """
    Return (home_xg, away_xg) estimates.
    Uses attack-vs-defence adjustment (Dixon-Coles style) with cached Understat data.
    Falls back to CSV goals-per-game if Understat has no data for the team.
    """
    try:
        home_stats = _cached_xg(league_slug, home_team_name)
        away_stats = _cached_xg(league_slug, away_team_name)
    except Exception:
        home_stats = {}
        away_stats = {}

    # Prefer home-specific xG; fall back to average
    home_att  = home_stats.get("xg_for_home")  or home_stats.get("xg_for_avg",  1.4)
    home_def  = home_stats.get("xg_against_home") or home_stats.get("xg_against_avg", 1.1)
    away_att  = away_stats.get("xg_for_away")  or away_stats.get("xg_for_avg",  1.1)
    away_def  = away_stats.get("xg_against_away") or away_stats.get("xg_against_avg", 1.3)

    # Adjust: home team's attack against away team's defence, and vice-versa
    home_xg = round((home_att + away_def) / 2 * 1.10, 2)   # +10% home advantage
    away_xg = round((away_att + home_def) / 2, 2)

    # If both stats are zeros (no Understat data for these teams), use CSV goals
    if home_xg < 0.3 or away_xg < 0.2:
        try:
            df = _cached_league_df(league_slug)
            h_form = compute_team_form(df, home_team_name)
            a_form = compute_team_form(df, away_team_name)
            home_xg = max(0.5, round(h_form.get("goals_scored", 1.4) * 0.85 * 1.10, 2))
            away_xg = max(0.3, round(a_form.get("goals_scored", 1.1) * 0.85, 2))
        except Exception:
            home_xg, away_xg = 1.4, 1.1

    return max(0.3, home_xg), max(0.2, away_xg)
