# ⚽ Football Intelligence

**AI-powered football betting intelligence platform** — real-time analytics, expected-score
predictions, value detection, explainable AI reasoning, a self-improving learning loop, and a
Champions League tournament simulator.

> Predictions are not guaranteed. This is not financial or betting advice. Bet responsibly. 18+

---

## What it does

- **League-first drill-through** homepage → league → matchday → match → full prediction
- **Prediction engine**: win/draw/loss probabilities, expected score (Poisson over xG), top
  scorelines, confidence, risk level, value rating
- **Explainable AI**: every recommendation comes with structured plain-English reasoning
  (positives, risks, rejected markets) — optional Claude API enrichment
- **No-stale-prediction rule**: predictions are blocked or downgraded when data is stale
- **Live Match Mode**: in-play probability updates with strict freshness gating
- **Agentic learning loop**: every prediction is evaluated post-match; accuracy, calibration,
  and ROI are tracked, and weight adjustments are suggested
- **Champions League module**: cross-league strength (UEFA coefficients), two-legged tie
  simulation, and a full Monte Carlo tournament simulator
- **Responsible gambling**: age gate, RG disclaimers, no guaranteed-win language (enforced)

## Data sources — no API keys required

| Source | Used for |
|--------|----------|
| [football-data.co.uk](https://www.football-data.co.uk) | Historical results + bookmaker odds (CSV) |
| [Understat](https://understat.com) | Expected goals (xG) |
| [TheSportsDB](https://www.thesportsdb.com) | Fixtures + recent results (free public key) |

Optional: set `ANTHROPIC_API_KEY` to enable Claude-generated explanations. Without it, the
rule-based explanation engine is used automatically.

---

## Tech stack

- **Backend**: FastAPI · SQLAlchemy (async) · SQLite · APScheduler · scipy/numpy
- **Frontend**: Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4
- **Theme**: Elite Dark Football Intelligence

---

## Quick start

### Backend

```bash
# from project root
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # macOS/Linux

pip install -r backend/requirements.txt

# Populate the database (seeds leagues + imports match data)
python -m scripts.populate_db --league premier-league

# Run the API (http://localhost:8000)
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                        # http://localhost:3000
```

---

## Useful scripts

| Script | Purpose |
|--------|---------|
| `python -m scripts.populate_db [--league SLUG] [--predict]` | Seed leagues + import matches |
| `python -m scripts.migrate_db` | Apply additive DB column migrations |
| `python -m scripts.backfill_predictions --limit N` | Generate predictions for finished matches |
| `python -m scripts.run_evaluation` | Evaluate predictions + print performance report |
| `python -m scripts.run_backtest --limit N` | Backtest harness with launch-readiness report |
| `python -m scripts.compliance_audit` | Verify PRD acceptance criteria before launch |

---

## API overview

```
GET  /matches/today | /upcoming | /live | /{id}
GET  /predictions/match/{id}          POST /predictions/match/{id}/generate
GET  /predictions/high-confidence | /value-bets
GET  /leagues/ | /leagues/slug/{slug} | /leagues/slug/{slug}/matches
GET  /performance/overview | /by-league | /by-bet-type | /calibration | /roi
GET  /cl/simulation | /cl/teams
POST /cl/match-prediction | /cl/two-leg-prediction
GET  /admin/data-health   POST /admin/evaluate   GET /admin/weight-suggestions
```

Interactive docs at `http://localhost:8000/docs`.

---

## Testing

```bash
python -m pytest tests/backend/ -v
```

79 tests covering the prediction engines, live processor, Champions League module, and
API integration.

---

## Project structure

```
backend/
  api/routes/          FastAPI routers
  data_pipeline/       ingestion (CSV, Understat, fixtures), validation, feature store
  prediction_engine/   models (outcome, score) + engines (confidence, risk, value, explanation) + live
  learning_loop/       evaluator, accuracy tracker, weight adjuster, backtester
  champions_league/    cross-league strength, two-leg predictor, tournament simulator
  db/                  models + async session
frontend/src/
  app/                 pages (home, league, match, live, picks, performance, champions-league)
  components/          match, league, prediction, champions-league, compliance, ui
scripts/               populate, migrate, backfill, evaluate, backtest, compliance audit
tests/backend/         unit + integration tests
```

---

## Status

MVP complete across all 8 PRD milestones: foundation, data pipeline, prediction engine,
frontend, AI explanation layer, learning loop, Champions League module, and beta-launch
hardening (backtesting, compliance audit, API tests, responsible gambling layer).

## Disclaimer

This product is a **betting insights and football analytics platform**, not a sportsbook.
It does not hold funds, process wagers, or place bets. Predictions are probabilistic and
carry risk. Always bet responsibly and within your means. 18+.
