# AI Football Betting Intelligence App — PRD v1.2 Summary

**Product:** Real-time AI football betting analytics platform  
**Stage:** MVP planning  
**Theme:** Elite Dark Football Intelligence  

## Supported competitions
- Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie (configurable)
- UEFA Champions League (separate module)

## Core prediction outputs
- Recommended bet, expected score, scoreline probabilities, win/draw/loss %, confidence, risk level, value rating, AI explanation

## Key design rules
- No stale predictions — block recommendation if critical data is missing
- No guaranteed-win language ever
- Live Match Mode in MVP with strict freshness thresholds (score: 10s, odds: 15s)
- League-first drill-through homepage: Home → League → Date → Match → Prediction

## Development milestones
1. Product Foundation
2. Data Pipeline
3. Prediction Engine MVP
4. Frontend MVP
5. AI Explanation Layer
6. Learning Loop
7. Champions League Module
8. Beta Launch

## Colour palette
| Purpose | Hex |
|---|---|
| Main background | #07111F |
| Primary action | #16A34A |
| Value accent | #F59E0B |
| Warning/risk | #F97316 |
| Danger/high risk | #EF4444 |
