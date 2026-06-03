"""
Backtester — Milestone 8
Runs the prediction engine over historical finished matches and measures
how the model would have performed. Distinct from the live learning loop:
the backtester is a one-shot evaluation harness for launch readiness.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import (
    Match, Prediction, PredictionEvaluation, MatchStatus, PredictionMode,
)
from backend.prediction_engine.predictor import generate_prediction
from backend.learning_loop.evaluator import evaluate_prediction


@dataclass
class BacktestReport:
    matches_tested: int = 0
    predictions_made: int = 0
    winner_correct: int = 0
    exact_correct: int = 0
    bets_recommended: int = 0
    bets_won: int = 0
    total_profit_loss: float = 0.0
    avg_goal_error: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def winner_accuracy(self) -> float:
        return round(self.winner_correct / self.predictions_made * 100, 1) if self.predictions_made else 0.0

    @property
    def exact_accuracy(self) -> float:
        return round(self.exact_correct / self.predictions_made * 100, 1) if self.predictions_made else 0.0

    @property
    def bet_win_rate(self) -> float:
        return round(self.bets_won / self.bets_recommended * 100, 1) if self.bets_recommended else 0.0

    @property
    def roi_pct(self) -> float:
        return round(self.total_profit_loss / self.bets_recommended * 100, 1) if self.bets_recommended else 0.0

    def to_dict(self) -> dict:
        return {
            "matches_tested": self.matches_tested,
            "predictions_made": self.predictions_made,
            "winner_accuracy_pct": self.winner_accuracy,
            "exact_score_accuracy_pct": self.exact_accuracy,
            "avg_goal_error": round(self.avg_goal_error, 2),
            "bets_recommended": self.bets_recommended,
            "bet_win_rate_pct": self.bet_win_rate,
            "roi_pct": self.roi_pct,
            "total_profit_loss_units": round(self.total_profit_loss, 2),
            "errors": self.errors[:10],
        }


async def run_backtest(db: AsyncSession, limit: int = 200) -> BacktestReport:
    """
    Backtest over finished matches. Generates predictions (force mode) and
    evaluates them against actual results.
    """
    report = BacktestReport()

    result = await db.execute(
        select(Match)
        .where(Match.status == MatchStatus.FINISHED)
        .where(Match.final_home_score.isnot(None))
        .order_by(Match.kickoff_time.desc())
        .limit(limit)
    )
    matches = result.scalars().all()
    report.matches_tested = len(matches)

    goal_errors: list[float] = []

    for match in matches:
        # Generate (or fetch existing) prediction
        existing = await db.execute(
            select(Prediction)
            .where(Prediction.match_id == match.id)
            .where(Prediction.mode == PredictionMode.PRE_MATCH)
            .order_by(Prediction.generated_at.desc())
            .limit(1)
        )
        pred = existing.scalar_one_or_none()

        if not pred:
            try:
                pred = await generate_prediction(db, match.id, force=True)
            except Exception as e:
                report.errors.append(f"Match {match.id}: {e}")
                continue

        if not pred:
            continue

        report.predictions_made += 1

        # Evaluate
        eval_result = await db.execute(
            select(PredictionEvaluation).where(PredictionEvaluation.prediction_id == pred.id)
        )
        ev = eval_result.scalar_one_or_none()
        if not ev:
            ev = await evaluate_prediction(db, pred, match)
        if not ev:
            continue

        if ev.winner_correct:
            report.winner_correct += 1
        if ev.exact_score_correct:
            report.exact_correct += 1
        if ev.goal_margin_error is not None:
            goal_errors.append(ev.goal_margin_error)
        if ev.bet_result in ("win", "loss"):
            report.bets_recommended += 1
            if ev.bet_result == "win":
                report.bets_won += 1
            report.total_profit_loss += ev.profit_loss_result or 0.0

    report.avg_goal_error = sum(goal_errors) / len(goal_errors) if goal_errors else 0.0
    return report
