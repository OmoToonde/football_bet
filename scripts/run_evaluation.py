"""
Run post-match evaluation on all finished matches in the DB.
Usage: python -m scripts.run_evaluation
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import AsyncSessionLocal
from backend.learning_loop.evaluator import run_batch_evaluation
from backend.learning_loop.accuracy_tracker import (
    get_overall_stats, get_stats_by_league, get_confidence_calibration, get_roi_summary,
)
from backend.learning_loop.weight_adjuster import suggest_weight_adjustments


async def main():
    print("=== Running Post-Match Evaluation ===\n")

    async with AsyncSessionLocal() as db:
        # Evaluate
        result = await run_batch_evaluation(db)
        print(f"Evaluated   : {result['evaluated']} new predictions")
        print(f"Already done: {result['skipped_already_done']}\n")

        # Stats
        stats = await get_overall_stats(db)
        if stats.get("total_predictions", 0) == 0:
            print("No evaluations in DB yet. Import matches with predictions first.")
            return

        print("=== Model Performance ===")
        print(f"Total predictions   : {stats['total_predictions']}")
        print(f"Bet recommendations : {stats['bet_recommendations']}")
        print(f"Winner accuracy     : {stats['winner_accuracy']}%")
        print(f"Bet win rate        : {stats['bet_win_rate']}%")
        print(f"Exact score accuracy: {stats['exact_score_accuracy']}%")
        print(f"Avg goal margin err : {stats['avg_goal_margin_error']} goals")
        print(f"Flat-stake ROI      : {stats['flat_stake_roi_units']} units ({stats['roi_per_bet_pct']}% per bet)\n")

        # By league
        leagues = await get_stats_by_league(db)
        if leagues:
            print("=== By League ===")
            for l in leagues:
                print(f"  {l['league']:<25} Winner: {l['winner_accuracy']}%  Bet win: {l['bet_win_rate']}%  ROI: {l['roi_units']:+.2f}")
            print()

        # Calibration
        cal = await get_confidence_calibration(db)
        if cal:
            print("=== Confidence Calibration ===")
            for c in cal:
                gap = c.get('calibration_gap')
                gap_str = f"  gap: {gap:+.1f}pp" if gap is not None else ""
                print(f"  {c['confidence_bracket']}: stated {c['stated_confidence_mid']}% → actual {c['actual_win_rate']}%{gap_str}")
            print()

        # ROI
        roi = await get_roi_summary(db)
        print("=== ROI Simulation ===")
        print(f"  All bets   : {roi['all_bets']['total']} bets, {roi['all_bets']['win_rate']}% wins, {roi['all_bets']['roi_pct']:+.1f}% ROI")
        print(f"  Value bets : {roi['value_bets_only']['total']} bets, {roi['value_bets_only']['win_rate']}% wins, {roi['value_bets_only']['roi_pct']:+.1f}% ROI\n")

        # Weight suggestions
        suggestions = await suggest_weight_adjustments(db)
        print("=== Weight Adjustment Suggestions ===")
        print(f"  Status: {suggestions['status']}")
        if suggestions['status'] == 'suggestions_ready':
            for reason in suggestions['reasoning']:
                print(f"  - {reason}")
        else:
            print(f"  {suggestions.get('message', '')}")

    print("\n=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
