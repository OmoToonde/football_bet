from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import League, Match

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("/")
async def get_leagues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(League))
    return {"leagues": [_format(l) for l in result.scalars().all()]}


@router.get("/{league_id}/matches")
async def get_league_matches(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match)
        .where(Match.league_id == league_id)
        .order_by(Match.kickoff_time)
    )
    return {"matches": result.scalars().all()}


def _format(l: League) -> dict:
    return {
        "id": l.id,
        "name": l.name,
        "country": l.country,
        "type": l.type,
        "season": l.season,
        "slug": l.slug,
    }
