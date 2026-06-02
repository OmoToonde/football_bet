"""
Background scheduler — refreshes data and regenerates predictions automatically.
Runs inside the FastAPI process using APScheduler.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.db.database import AsyncSessionLocal
from backend.data_pipeline.ingestion.seed_leagues import seed_leagues
from backend.data_pipeline.ingestion.match_importer import import_league
from backend.db.models import Match, MatchStatus
from backend.prediction_engine.predictor import generate_prediction
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _refresh_all():
    """Re-import match data and refresh predictions for upcoming matches."""
    logger.info("Scheduler: starting data refresh …")
    try:
        async with AsyncSessionLocal() as db:
            slug_to_id = await seed_leagues(db)
            for slug, league_id in slug_to_id.items():
                try:
                    await import_league(db, slug, league_id)
                except Exception as e:
                    logger.warning(f"Scheduler: import failed for {slug}: {e}")

            # Regenerate predictions for next 24h
            from datetime import datetime, timedelta, timezone
            cutoff = datetime.now(timezone.utc) + timedelta(hours=24)
            result = await db.execute(
                select(Match)
                .where(Match.status == MatchStatus.SCHEDULED)
                .where(Match.kickoff_time <= cutoff)
            )
            for match in result.scalars().all():
                try:
                    await generate_prediction(db, match.id)
                except Exception as e:
                    logger.warning(f"Scheduler: prediction failed for match {match.id}: {e}")

        # Evaluate any newly finished matches
        async with AsyncSessionLocal() as db:
            from backend.learning_loop.evaluator import run_batch_evaluation
            result = await run_batch_evaluation(db)
            logger.info(f"Scheduler: evaluated {result['evaluated']} predictions")

        logger.info("Scheduler: refresh complete")
    except Exception as e:
        logger.error(f"Scheduler: refresh error: {e}")


def start_scheduler():
    """Register jobs and start the scheduler. Call from FastAPI startup."""
    scheduler.add_job(
        _refresh_all,
        trigger=IntervalTrigger(hours=6),
        id="full_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — full refresh every 6 hours")


def stop_scheduler():
    scheduler.shutdown(wait=False)
