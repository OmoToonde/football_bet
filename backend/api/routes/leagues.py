from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from backend.db.database import get_db
from backend.db.models import League, Match, MatchStatus, Prediction, PredictionMode

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("/")
async def get_leagues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(League))
    leagues = result.scalars().all()

    enriched = []
    for league in leagues:
        enriched.append(await _format_league(league, db))
    return {"leagues": enriched}


@router.get("/slug/{slug}")
async def get_league_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(League).where(League.slug == slug))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail=f"League '{slug}' not found")
    return await _format_league(league, db)


@router.get("/slug/{slug}/matches")
async def get_league_matches_by_slug(
    slug: str,
    days: int = 14,
    db: AsyncSession = Depends(get_db),
):
    """Return upcoming + recent matches for a league, with prediction summaries."""
    result = await db.execute(select(League).where(League.slug == slug))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail=f"League '{slug}' not found")

    cutoff_past   = datetime.utcnow() - timedelta(days=7)
    cutoff_future = datetime.utcnow() + timedelta(days=days)

    matches_result = await db.execute(
        select(Match)
        .where(Match.league_id == league.id)
        .where(Match.kickoff_time >= cutoff_past)
        .where(Match.kickoff_time <= cutoff_future)
        .order_by(Match.kickoff_time)
    )
    matches = matches_result.scalars().all()

    from backend.api.routes.matches import _enrich
    return {
        "league": _format_league_basic(league),
        "matches": await _enrich(matches, db),
    }


@router.get("/{league_id}/matches")
async def get_league_matches(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match)
        .where(Match.league_id == league_id)
        .where(Match.kickoff_time >= datetime.utcnow() - timedelta(days=7))
        .order_by(Match.kickoff_time)
        .limit(30)
    )
    matches = result.scalars().all()
    from backend.api.routes.matches import _enrich
    return {"matches": await _enrich(matches, db)}


async def _format_league(league: League, db: AsyncSession) -> dict:
    """League card data including live/upcoming counts and best prediction."""
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)

    upcoming_count = (await db.execute(
        select(func.count()).where(
            Match.league_id == league.id,
            Match.kickoff_time >= now,
            Match.kickoff_time <= now + timedelta(days=7),
            Match.status == MatchStatus.SCHEDULED,
        )
    )).scalar() or 0

    live_count = (await db.execute(
        select(func.count()).where(
            Match.league_id == league.id,
            Match.status == MatchStatus.LIVE,
        )
    )).scalar() or 0

    # Highest confidence prediction today
    next_match = (await db.execute(
        select(Match)
        .where(Match.league_id == league.id)
        .where(Match.kickoff_time >= now)
        .where(Match.status == MatchStatus.SCHEDULED)
        .order_by(Match.kickoff_time)
        .limit(1)
    )).scalar_one_or_none()

    best_pred = None
    if next_match:
        best_pred = (await db.execute(
            select(Prediction)
            .where(Prediction.match_id == next_match.id)
            .where(Prediction.mode == PredictionMode.PRE_MATCH)
            .order_by(Prediction.confidence_score.desc())
            .limit(1)
        )).scalar_one_or_none()

    d = _format_league_basic(league)
    d.update({
        "upcoming_matches": upcoming_count,
        "live_now": live_count,
        "next_kickoff": next_match.kickoff_time.isoformat() if next_match else None,
        "best_pick": best_pred.recommended_bet if best_pred else None,
        "highest_confidence": best_pred.confidence_score if best_pred else None,
    })
    return d


def _format_league_basic(l: League) -> dict:
    return {
        "id": l.id,
        "name": l.name,
        "country": l.country,
        "type": l.type,
        "season": l.season,
        "slug": l.slug,
    }
