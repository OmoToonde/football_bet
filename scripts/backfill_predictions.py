"""
Backfill predictions for recent finished matches — gives the learning loop data to work with.
In production, predictions are made BEFORE matches. This script simulates that by predicting
finished matches so we can measure how well the model would have done.

Usage: python -m scripts.backfill_predictions [--limit 50]
"""
import asyncio, sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import AsyncSessionLocal
from backend.db.models import Match, MatchStatus, Prediction, PredictionMode
from backend.prediction_engine.predictor import generate_prediction
from sqlalchemy import select


async def backfill(limit: int = 50):
    print(f"=== Backfilling predictions for up to {limit} finished matches ===\n")
    async with AsyncSessionLocal() as db:
        # Finished matches that don't yet have a prediction
        existing_pred_match_ids = set(
            row[0] for row in (await db.execute(
                select(Prediction.match_id)
                .where(Prediction.mode == PredictionMode.PRE_MATCH)
            )).all()
        )

        result = await db.execute(
            select(Match)
            .where(Match.status == MatchStatus.FINISHED)
            .where(Match.final_home_score.isnot(None))
            .order_by(Match.kickoff_time.desc())
            .limit(limit * 2)  # fetch extra since some will be blocked
        )
        candidates = [m for m in result.scalars().all() if m.id not in existing_pred_match_ids]

        print(f"Found {len(candidates)} finished matches without predictions\n")

        generated = 0
        for match in candidates[:limit]:
            try:
                pred = await generate_prediction(db, match.id, force=True)
                if pred:
                    generated += 1
            except Exception as e:
                pass  # silent; some matches will be blocked due to freshness

        print(f"\nGenerated {generated} predictions")

    print("=== Done ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    asyncio.run(backfill(args.limit))
