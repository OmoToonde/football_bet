"""
Run the backtest harness and print a launch-readiness report.
Usage: python -m scripts.run_backtest [--limit 200]
"""
import asyncio, sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import AsyncSessionLocal
from backend.learning_loop.backtester import run_backtest


async def main(limit: int):
    print(f"=== Backtest (up to {limit} finished matches) ===\n")
    async with AsyncSessionLocal() as db:
        report = await run_backtest(db, limit=limit)
        r = report.to_dict()

        print(f"Matches tested      : {r['matches_tested']}")
        print(f"Predictions made    : {r['predictions_made']}")
        print(f"Winner accuracy     : {r['winner_accuracy_pct']}%")
        print(f"Exact score accuracy: {r['exact_score_accuracy_pct']}%")
        print(f"Avg goal error      : {r['avg_goal_error']} goals")
        print(f"Bets recommended    : {r['bets_recommended']}")
        print(f"Bet win rate        : {r['bet_win_rate_pct']}%")
        print(f"ROI                 : {r['roi_pct']}% ({r['total_profit_loss_units']} units)")
        if r["errors"]:
            print(f"\nErrors ({len(r['errors'])}):")
            for e in r["errors"]:
                print(f"  - {e}")
    print("\n=== Done ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(main(args.limit))
