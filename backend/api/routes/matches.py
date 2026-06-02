from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date

from backend.db.database import get_db
from backend.db.models import Match, League, Team, MatchStatus

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/today")
async def get_today_matches(db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = await db.execute(
        select(Match)
        .where(Match.kickoff_time >= datetime.combine(today, datetime.min.time()))
        .where(Match.kickoff_time < datetime.combine(today, datetime.max.time()))
        .order_by(Match.kickoff_time)
    )
    matches = result.scalars().all()
    return {"matches": [_format_match(m) for m in matches]}


@router.get("/upcoming")
async def get_upcoming_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match)
        .where(Match.kickoff_time >= datetime.utcnow())
        .where(Match.status == MatchStatus.SCHEDULED)
        .order_by(Match.kickoff_time)
        .limit(50)
    )
    matches = result.scalars().all()
    return {"matches": [_format_match(m) for m in matches]}


@router.get("/live")
async def get_live_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match).where(Match.status == MatchStatus.LIVE)
    )
    matches = result.scalars().all()
    return {"matches": [_format_match(m) for m in matches]}


@router.get("/{match_id}")
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return _format_match(match)


def _format_match(m: Match) -> dict:
    return {
        "id": m.id,
        "home_team_id": m.home_team_id,
        "away_team_id": m.away_team_id,
        "league_id": m.league_id,
        "kickoff_time": m.kickoff_time.isoformat() if m.kickoff_time else None,
        "status": m.status.value,
        "home_score": m.final_home_score,
        "away_score": m.final_away_score,
    }
