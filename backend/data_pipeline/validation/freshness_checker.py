"""
Data Freshness Checker
Hard rule: if critical match data is stale/missing, block the prediction.
"""
from datetime import datetime, timezone
from backend.db.models import FreshnessStatus
from backend.config import settings


def _age_seconds(dt: datetime | None) -> float:
    if dt is None:
        return float("inf")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds()


def check_pre_match_freshness(
    odds_updated_at: datetime | None,
    injury_updated_at: datetime | None,
    lineup_updated_at: datetime | None,
    stats_updated_at: datetime | None,
) -> FreshnessStatus:
    odds_age = _age_seconds(odds_updated_at)
    injury_age = _age_seconds(injury_updated_at)

    # Odds missing entirely → block
    if odds_age == float("inf"):
        return FreshnessStatus.BLOCKED

    stale = settings.pre_match_stale_threshold

    if odds_age > stale * 2 or injury_age > stale * 3:
        return FreshnessStatus.STALE

    if odds_age > stale or injury_age > stale * 1.5:
        return FreshnessStatus.INCOMPLETE

    if lineup_updated_at is None:
        return FreshnessStatus.ACCEPTABLE

    return FreshnessStatus.FRESH


def check_live_freshness(
    score_updated_at: datetime | None,
    odds_updated_at: datetime | None,
    stats_updated_at: datetime | None,
) -> FreshnessStatus:
    score_age = _age_seconds(score_updated_at)
    odds_age = _age_seconds(odds_updated_at)
    stats_age = _age_seconds(stats_updated_at)

    # Critical: score or odds too old → block live recommendation
    if score_age > settings.live_score_stale_threshold:
        return FreshnessStatus.BLOCKED
    if odds_age > settings.live_odds_stale_threshold:
        return FreshnessStatus.LIVE_DELAYED

    # Stats delay → downgrade but don't block
    if stats_age > settings.live_stats_stale_threshold:
        return FreshnessStatus.ACCEPTABLE

    return FreshnessStatus.FRESH


def should_block_prediction(status: FreshnessStatus) -> bool:
    return status in (FreshnessStatus.BLOCKED, FreshnessStatus.STALE)


def should_block_live_recommendation(status: FreshnessStatus) -> bool:
    return status in (FreshnessStatus.BLOCKED, FreshnessStatus.LIVE_DELAYED)
