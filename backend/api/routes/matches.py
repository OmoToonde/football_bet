from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timedelta

from backend.db.database import get_db
from backend.db.models import Match, League, Team, MatchStatus, Prediction, PredictionMode

router = APIRouter(prefix="/matches", tags=["matches"])


async def _enrich(matches: list[Match], db: AsyncSession) -> list[dict]:
    """Fetch team + league names for a list of matches."""
    if not matches:
        return []

    team_ids = {m.home_team_id for m in matches} | {m.away_team_id for m in matches}
    league_ids = {m.league_id for m in matches}

    teams = {
        t.id: t for t in
        (await db.execute(select(Team).where(Team.id.in_(team_ids)))).scalars().all()
    }
    leagues = {
        l.id: l for l in
        (await db.execute(select(League).where(League.id.in_(league_ids)))).scalars().all()
    }

    # Latest prediction per match (one query)
    match_ids = [m.id for m in matches]
    pred_rows = (await db.execute(
        select(Prediction)
        .where(Prediction.match_id.in_(match_ids))
        .where(Prediction.mode == PredictionMode.PRE_MATCH)
        .order_by(Prediction.generated_at.desc())
    )).scalars().all()
    # Keep only most recent per match
    preds: dict[int, Prediction] = {}
    for p in pred_rows:
        if p.match_id not in preds:
            preds[p.match_id] = p

    return [_format_match(m, teams, leagues, preds.get(m.id)) for m in matches]


def _format_match(
    m: Match,
    teams: dict = None,
    leagues: dict = None,
    pred: Prediction = None,
) -> dict:
    home = teams.get(m.home_team_id) if teams else None
    away = teams.get(m.away_team_id) if teams else None
    league = leagues.get(m.league_id) if leagues else None

    base = {
        "id": m.id,
        "home_team_id": m.home_team_id,
        "home_team": home.name if home else None,
        "home_logo": home.logo_url if home else None,
        "away_team_id": m.away_team_id,
        "away_team": away.name if away else None,
        "away_logo": away.logo_url if away else None,
        "league_id": m.league_id,
        "league_name": league.name if league else None,
        "league_slug": league.slug if league else None,
        "kickoff_time": m.kickoff_time.isoformat() if m.kickoff_time else None,
        "venue": m.venue,
        "status": m.status.value,
        "home_score": m.final_home_score,
        "away_score": m.final_away_score,
    }

    if pred:
        base["prediction_summary"] = {
            "recommended_bet": pred.recommended_bet,
            "expected_score": pred.expected_score,
            "confidence_score": pred.confidence_score,
            "risk_level": pred.risk_level.value,
            "value_rating": pred.value_rating,
            "data_freshness_status": pred.data_freshness_status.value,
        }
    else:
        base["prediction_summary"] = None

    return base


@router.get("/today")
async def get_today_matches(db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = await db.execute(
        select(Match)
        .where(Match.kickoff_time >= datetime.combine(today, datetime.min.time()))
        .where(Match.kickoff_time < datetime.combine(today, datetime.max.time()))
        .order_by(Match.kickoff_time)
    )
    return {"matches": await _enrich(result.scalars().all(), db)}


@router.get("/upcoming")
async def get_upcoming_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match)
        .where(Match.kickoff_time >= datetime.utcnow())
        .where(Match.status == MatchStatus.SCHEDULED)
        .order_by(Match.kickoff_time)
        .limit(50)
    )
    return {"matches": await _enrich(result.scalars().all(), db)}


@router.get("/live")
async def get_live_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match).where(Match.status == MatchStatus.LIVE)
    )
    return {"matches": await _enrich(result.scalars().all(), db)}


@router.get("/recent")
async def get_recent_matches(days: int = 45, db: AsyncSession = Depends(get_db)):
    """Recent finished + upcoming matches across all leagues, for a FotMob-style list."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Match)
        .where(Match.kickoff_time >= now - timedelta(days=days))
        .where(Match.kickoff_time <= now + timedelta(days=14))
        .order_by(Match.kickoff_time.desc())
        .limit(200)
    )
    enriched = await _enrich(result.scalars().all(), db)

    # Dedupe matches that appear under two data-source name formats
    # (e.g. "West Ham United" vs "West Ham"). Key on date + first 4 chars of each team.
    seen: set = set()
    deduped = []
    for m in enriched:
        d = (m.get("kickoff_time") or "")[:10]
        h = (m.get("home_team") or "")[:4].lower()
        a = (m.get("away_team") or "")[:4].lower()
        key = (d, h, a)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)

    return {"matches": deduped[:120]}


@router.get("/{match_id}")
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    enriched = await _enrich([match], db)
    return enriched[0]
