"""
Match Importer — Milestone 2
Combines three data sources (all free, no API key):
  1. football-data.co.uk  → historical results + odds
  2. TheSportsDB free API → upcoming fixtures
  3. Understat            → xG statistics

Writes League, Team, Match, MatchDataSnapshot rows into the DB.
"""
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import Match, MatchDataSnapshot, MatchStatus, FreshnessStatus
from backend.data_pipeline.ingestion.seed_leagues import upsert_team
from backend.data_pipeline.ingestion.football_data_co_uk import (
    fetch_league_results, get_odds_for_match,
)
from backend.data_pipeline.ingestion.fixtures_scraper import (
    fetch_next_fixtures, fetch_last_results,
)
from backend.data_pipeline.ingestion.understat_scraper import get_team_xg_stats

# Map our league slugs → country strings (for Team.country)
LEAGUE_COUNTRIES = {
    "premier-league":   "England",
    "la-liga":          "Spain",
    "serie-a":          "Italy",
    "bundesliga":       "Germany",
    "ligue-1":          "France",
    "eredivisie":       "Netherlands",
    "champions-league": "Europe",
}


async def import_league(
    db: AsyncSession,
    league_slug: str,
    league_id: int,
) -> int:
    """
    Import historical results + upcoming fixtures for one league.
    Returns count of new matches added.
    """
    country = LEAGUE_COUNTRIES.get(league_slug, "Unknown")
    added = 0

    # ── 1. Historical results from football-data.co.uk ──────────────────
    print(f"\n  [{league_slug}] Fetching historical data from football-data.co.uk …")
    try:
        hist_df = fetch_league_results(league_slug)
        print(f"    Got {len(hist_df)} historical rows")
    except Exception as e:
        print(f"    ! Could not fetch CSV: {e}")
        hist_df = None

    # ── 2. Upcoming fixtures from TheSportsDB ───────────────────────────
    print(f"  [{league_slug}] Fetching upcoming fixtures from TheSportsDB …")
    upcoming = fetch_next_fixtures(league_slug)
    print(f"    Got {len(upcoming)} upcoming fixtures")

    # ── 3. Recent results from TheSportsDB (backup) ─────────────────────
    print(f"  [{league_slug}] Fetching recent results from TheSportsDB …")
    recent_results = fetch_last_results(league_slug)
    print(f"    Got {len(recent_results)} recent results")

    # Combine all matches to process
    all_matches_raw: list[dict] = []

    if hist_df is not None:
        for _, row in hist_df.iterrows():
            if not row.get("HomeTeam") or not row.get("AwayTeam"):
                continue
            all_matches_raw.append({
                "home_team": row["HomeTeam"],
                "away_team": row["AwayTeam"],
                "kickoff_time": row["Date"].to_pydatetime() if hasattr(row["Date"], "to_pydatetime") else row["Date"],
                "home_score": int(row.get("FTHG", 0) or 0),
                "away_score": int(row.get("FTAG", 0) or 0),
                "status": MatchStatus.FINISHED,
                "odds_home": float(row.get("B365H", 0) or 0),
                "odds_draw": float(row.get("B365D", 0) or 0),
                "odds_away": float(row.get("B365A", 0) or 0),
            })

    for m in recent_results:
        all_matches_raw.append({**m, "status": MatchStatus.FINISHED,
                                 "odds_home": 0.0, "odds_draw": 0.0, "odds_away": 0.0})

    for m in upcoming:
        all_matches_raw.append({**m, "home_score": None, "away_score": None,
                                 "status": MatchStatus.SCHEDULED,
                                 "odds_home": 0.0, "odds_draw": 0.0, "odds_away": 0.0})

    # ── Upsert into DB ───────────────────────────────────────────────────
    for m in all_matches_raw:
        home_id = await upsert_team(db, m["home_team"], country, league_id)
        away_id = await upsert_team(db, m["away_team"], country, league_id)

        # Check if match already exists
        existing = await db.execute(
            select(Match)
            .where(Match.home_team_id == home_id)
            .where(Match.away_team_id == away_id)
            .where(Match.league_id == league_id)
            .where(Match.kickoff_time == m["kickoff_time"])
        )
        if existing.scalar_one_or_none():
            continue

        match = Match(
            league_id=league_id,
            home_team_id=home_id,
            away_team_id=away_id,
            kickoff_time=m["kickoff_time"],
            venue=m.get("venue", ""),
            status=m["status"],
            final_home_score=m.get("home_score"),
            final_away_score=m.get("away_score"),
        )
        db.add(match)
        await db.flush()

        # Attach a data snapshot with odds (if available)
        odds_data = {}
        if hist_df is not None and m.get("odds_home"):
            odds_data = {
                "home_odds": m["odds_home"],
                "draw_odds": m["odds_draw"],
                "away_odds": m["odds_away"],
            }

        now = datetime.now(timezone.utc)
        snapshot = MatchDataSnapshot(
            match_id=match.id,
            collected_at=now,
            odds_updated_at=now if odds_data else None,
            freshness_status=(
                FreshnessStatus.FRESH if m["status"] == MatchStatus.SCHEDULED
                else FreshnessStatus.ACCEPTABLE
            ),
            raw_data=json.dumps(odds_data) if odds_data else None,
        )
        db.add(snapshot)
        added += 1

    await db.commit()
    print(f"  [{league_slug}] Added {added} new matches")
    return added
