"""
Master populate script — Milestone 2
Run once to seed leagues, import all match data, and generate predictions
for upcoming fixtures.

Usage:
    cd "Football Bet"
    python -m scripts.populate_db
    python -m scripts.populate_db --league premier-league   # single league
    python -m scripts.populate_db --predict                 # also run predictions
"""
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import init_db, AsyncSessionLocal
from backend.data_pipeline.ingestion.seed_leagues import seed_leagues
from backend.data_pipeline.ingestion.match_importer import import_league
from backend.db.models import Match, MatchStatus
from sqlalchemy import select


async def populate(target_league: str | None = None, run_predictions: bool = False):
    print("=== Football Intelligence — Database Populate ===\n")

    # Initialise tables
    await init_db()
    print("✓ Database tables ready\n")

    async with AsyncSessionLocal() as db:
        # 1. Seed leagues
        print("Step 1: Seeding leagues …")
        slug_to_id = await seed_leagues(db)
        print(f"  ✓ {len(slug_to_id)} leagues in database\n")

        # 2. Import match data for each league
        print("Step 2: Importing match data …")
        total_added = 0
        for slug, league_id in slug_to_id.items():
            if target_league and slug != target_league:
                continue
            try:
                added = await import_league(db, slug, league_id)
                total_added += added
            except Exception as e:
                print(f"  ! Error importing {slug}: {e}")
        print(f"\n  ✓ Total new matches added: {total_added}\n")

        # 3. Generate predictions for upcoming matches
        if run_predictions:
            print("Step 3: Generating predictions for upcoming fixtures …")
            from backend.prediction_engine.predictor import generate_prediction

            result = await db.execute(
                select(Match)
                .where(Match.status == MatchStatus.SCHEDULED)
                .order_by(Match.kickoff_time)
                .limit(50)
            )
            upcoming = result.scalars().all()
            print(f"  Found {len(upcoming)} upcoming matches\n")

            pred_count = 0
            for match in upcoming:
                try:
                    pred = await generate_prediction(db, match.id)
                    if pred:
                        pred_count += 1
                except Exception as e:
                    print(f"  ! Error predicting match {match.id}: {e}")

            print(f"\n  ✓ Predictions generated: {pred_count}\n")
        else:
            print("Step 3: Skipped (pass --predict to generate predictions)\n")

    print("=== Done ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate the football_bet database")
    parser.add_argument("--league", help="Only import this league slug", default=None)
    parser.add_argument("--predict", action="store_true", help="Also generate predictions")
    args = parser.parse_args()
    asyncio.run(populate(target_league=args.league, run_predictions=args.predict))
