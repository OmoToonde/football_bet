"""
Populate Team.logo_url with real club crests from TheSportsDB.

The free key throttles searchteams after ~35 calls and lookup_all_teams returns the
wrong roster, so we fetch ONLY the distinct teams that appear in recent matches
(deduped by normalised name) via per-team search, which returns correct data.

Usage: python -m scripts.fetch_badges
"""
import asyncio, sys, os, time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import AsyncSessionLocal
from backend.db.models import Team, League, Match
from backend.data_pipeline.ingestion.team_badges import search_team_badge, _norm
from sqlalchemy import select, update

LEAGUE_COUNTRY = {
    "premier-league": "England", "la-liga": "Spain", "serie-a": "Italy",
    "bundesliga": "Germany", "ligue-1": "France", "eredivisie": "Netherlands",
}


async def main():
    print("=== Fetching team badges (targeted per-team search) ===\n")
    async with AsyncSessionLocal() as db:
        await db.execute(update(Team).values(logo_url=None))
        await db.commit()

        leagues = {l.id: l for l in (await db.execute(select(League))).scalars().all()}

        # Teams that appear in recent matches (last 45 days)
        cutoff = datetime.utcnow() - timedelta(days=45)
        matches = (await db.execute(
            select(Match).where(Match.kickoff_time >= cutoff)
        )).scalars().all()
        team_ids = set()
        for m in matches:
            team_ids.update([m.home_team_id, m.away_team_id])

        teams = (await db.execute(
            select(Team).where(Team.id.in_(team_ids))
        )).scalars().all()

        # Dedupe by normalised name; keep one representative, then apply badge to all aliases
        by_norm: dict[str, list[Team]] = {}
        for t in teams:
            by_norm.setdefault(_norm(t.name), []).append(t)

        print(f"  {len(teams)} teams in recent matches, {len(by_norm)} unique clubs\n")

        stored = 0
        consecutive_empty = 0
        for norm_name, group in sorted(by_norm.items()):
            rep = group[0]
            league = leagues.get(rep.league_id)
            country = LEAGUE_COUNTRY.get(league.slug) if league else None
            badge = search_team_badge(rep.name, expected_country=country)
            if badge:
                for t in group:        # apply to all name-variants of this club
                    t.logo_url = badge
                stored += 1
                consecutive_empty = 0
                print(f"  [+] {rep.name}")
            else:
                consecutive_empty += 1
                print(f"  [ ] {rep.name}")
                if consecutive_empty >= 8:
                    print("  ! many consecutive misses — likely throttled, stopping early")
                    break
            time.sleep(1.0)
        await db.commit()
        print(f"\n=== Done: {stored} clubs badged ===")


if __name__ == "__main__":
    asyncio.run(main())
