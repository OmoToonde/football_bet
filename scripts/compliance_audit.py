"""
Compliance Audit — Milestone 8
Verifies the product meets PRD acceptance criteria before beta launch:
  - No guaranteed-win language in any stored explanation (section 37.6)
  - Every prediction has a freshness status and confidence (section 37.1)
  - Probabilities sum correctly
  - Responsible gambling disclaimers present

Usage: python -m scripts.compliance_audit
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import AsyncSessionLocal
from backend.db.models import Prediction
from backend.prediction_engine.engines.explanation_engine import FORBIDDEN_PHRASES
from sqlalchemy import select


async def audit():
    print("=== Compliance Audit (PRD acceptance criteria) ===\n")
    passed = 0
    failed = 0
    checks: list[tuple[str, bool, str]] = []

    async with AsyncSessionLocal() as db:
        preds = (await db.execute(select(Prediction))).scalars().all()

        if not preds:
            print("No predictions in DB — run backfill or populate first.")
            return

        # ── Check 1: No forbidden language ──────────────────────────────
        violations = []
        for p in preds:
            text = (p.explanation or "").lower()
            for phrase in FORBIDDEN_PHRASES:
                if phrase in text:
                    violations.append((p.id, phrase))
        checks.append((
            "No guaranteed-win language in explanations",
            len(violations) == 0,
            f"{len(violations)} violations" if violations else f"{len(preds)} predictions clean",
        ))

        # ── Check 2: Every prediction has freshness status ──────────────
        missing_freshness = [p.id for p in preds if not p.data_freshness_status]
        checks.append((
            "Every prediction has a data freshness status",
            len(missing_freshness) == 0,
            f"{len(missing_freshness)} missing" if missing_freshness else "all present",
        ))

        # ── Check 3: Every prediction has confidence + risk ─────────────
        missing_conf = [p.id for p in preds if p.confidence_score is None]
        missing_risk = [p.id for p in preds if not p.risk_level]
        checks.append((
            "Every prediction has confidence + risk level",
            len(missing_conf) == 0 and len(missing_risk) == 0,
            f"{len(missing_conf)} no conf, {len(missing_risk)} no risk"
            if (missing_conf or missing_risk) else "all present",
        ))

        # ── Check 4: Probabilities sum to ~1 ────────────────────────────
        bad_probs = []
        for p in preds:
            if None in (p.home_win_probability, p.draw_probability, p.away_win_probability):
                continue
            total = p.home_win_probability + p.draw_probability + p.away_win_probability
            if abs(total - 1.0) > 0.02:
                bad_probs.append((p.id, round(total, 3)))
        checks.append((
            "Win/draw/loss probabilities sum to 1.0",
            len(bad_probs) == 0,
            f"{len(bad_probs)} out of range" if bad_probs else "all valid",
        ))

        # ── Check 5: Disclaimer present in explanations ─────────────────
        no_disclaimer = [
            p.id for p in preds
            if p.explanation and "bet responsibly" not in p.explanation.lower()
        ]
        checks.append((
            "Responsible gambling disclaimer present",
            len(no_disclaimer) == 0,
            f"{len(no_disclaimer)} missing disclaimer" if no_disclaimer else "all present",
        ))

        # ── Check 6: No-bet state exists in vocabulary ──────────────────
        has_no_bet = any(p.recommended_bet == "No Bet Recommended" for p in preds)
        checks.append((
            "No-Bet-Recommended state is in use",
            has_no_bet,
            "present" if has_no_bet else "never used — verify low-confidence handling",
        ))

    # Report
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        symbol = "[+]" if ok else "[X]"
        print(f"  {symbol} {status}: {name}")
        print(f"        {detail}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n=== {passed} passed, {failed} failed ===")
    if failed == 0:
        print("All compliance checks passed. Ready for beta.")
    else:
        print("Compliance issues found — resolve before launch.")
    return failed == 0


if __name__ == "__main__":
    asyncio.run(audit())
