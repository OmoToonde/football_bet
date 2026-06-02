"""
Seeds the supported leagues and their teams into the database.
Runs once on first populate; safe to re-run (upserts by slug).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import League, Team

LEAGUES = [
    {"name": "Premier League",   "country": "England",     "slug": "premier-league",   "type": "domestic"},
    {"name": "La Liga",          "country": "Spain",       "slug": "la-liga",           "type": "domestic"},
    {"name": "Serie A",          "country": "Italy",       "slug": "serie-a",           "type": "domestic"},
    {"name": "Bundesliga",       "country": "Germany",     "slug": "bundesliga",        "type": "domestic"},
    {"name": "Ligue 1",          "country": "France",      "slug": "ligue-1",           "type": "domestic"},
    {"name": "Eredivisie",       "country": "Netherlands", "slug": "eredivisie",        "type": "domestic"},
    {"name": "Champions League", "country": "Europe",      "slug": "champions-league",  "type": "european"},
]

SEASON = "2024/25"


async def seed_leagues(db: AsyncSession) -> dict[str, int]:
    """Insert leagues if they don't exist. Returns {slug: league_id}."""
    slug_to_id: dict[str, int] = {}

    for data in LEAGUES:
        result = await db.execute(
            select(League).where(League.slug == data["slug"])
        )
        league = result.scalar_one_or_none()

        if not league:
            league = League(
                name=data["name"],
                country=data["country"],
                type=data["type"],
                season=SEASON,
                slug=data["slug"],
            )
            db.add(league)
            await db.flush()
            print(f"  + League: {league.name}")
        else:
            print(f"  = League already exists: {league.name}")

        slug_to_id[data["slug"]] = league.id

    await db.commit()
    return slug_to_id


async def upsert_team(db: AsyncSession, name: str, country: str, league_id: int) -> int:
    """Insert team if it doesn't exist. Returns team id."""
    result = await db.execute(
        select(Team).where(Team.name == name).where(Team.league_id == league_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        team = Team(name=name, country=country, league_id=league_id)
        db.add(team)
        await db.flush()
    return team.id
