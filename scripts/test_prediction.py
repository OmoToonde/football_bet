"""
Quick smoke test — generates one prediction for the most recent match in the DB
to verify the full pipeline works end-to-end.

Usage:
    python -m scripts.test_prediction
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import AsyncSessionLocal
from backend.db.models import Match, Team, League
from backend.prediction_engine.predictor import generate_prediction
from sqlalchemy import select


async def run_test():
    async with AsyncSessionLocal() as db:
        # Pick the most recently added match
        result = await db.execute(
            select(Match).order_by(Match.id.desc()).limit(1)
        )
        match = result.scalar_one_or_none()
        if not match:
            print("No matches in DB. Run populate_db first.")
            return

        home = (await db.execute(select(Team).where(Team.id == match.home_team_id))).scalar_one()
        away = (await db.execute(select(Team).where(Team.id == match.away_team_id))).scalar_one()
        league = (await db.execute(select(League).where(League.id == match.league_id))).scalar_one()

        print(f"\nTest match: {home.name} vs {away.name} ({league.name})")
        print(f"Kickoff: {match.kickoff_time}  Status: {match.status.value}\n")

        pred = await generate_prediction(db, match.id)
        if not pred:
            print("Prediction blocked (stale data or match not found)")
            return

        print("\n=== PREDICTION OUTPUT ===")
        print(f"Recommended Bet : {pred.recommended_bet}")
        print(f"Expected Score  : {pred.expected_score}")
        print(f"Home win        : {pred.home_win_probability:.1%}")
        print(f"Draw            : {pred.draw_probability:.1%}")
        print(f"Away win        : {pred.away_win_probability:.1%}")
        print(f"Home xG         : {pred.home_xg:.2f}   Away xG: {pred.away_xg:.2f}")
        print(f"Confidence      : {pred.confidence_score:.0f}%")
        print(f"Risk            : {pred.risk_level.value}")
        print(f"Value Rating    : {pred.value_rating}/10")
        print(f"Freshness       : {pred.data_freshness_status.value}")
        print(f"\nExplanation:\n{pred.explanation}")


if __name__ == "__main__":
    asyncio.run(run_test())
