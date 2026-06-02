"""
Head-to-Head metrics derived from football-data.co.uk CSVs.
No API key required.
"""
import pandas as pd
from backend.data_pipeline.feature_store.cache import feature_cache
from backend.data_pipeline.ingestion.football_data_co_uk import fetch_league_results


def get_h2h_record(
    league_slug: str,
    home_team: str,
    away_team: str,
    last_n: int = 10,
) -> dict:
    """
    Return head-to-head stats between two teams (both home and away meetings).
    Uses cached league CSV to avoid repeated downloads.
    """
    cache_key = f"csv_{league_slug}"
    df = feature_cache.get(cache_key)
    if df is None:
        try:
            df = fetch_league_results(league_slug)
            feature_cache.set(cache_key, df)
        except Exception:
            return _empty_h2h()

    # All meetings between the two teams in either direction
    mask = (
        ((df["HomeTeam"] == home_team) & (df["AwayTeam"] == away_team)) |
        ((df["HomeTeam"] == away_team) & (df["AwayTeam"] == home_team))
    )
    meetings = df[mask].sort_values("Date", ascending=False).head(last_n)

    if meetings.empty:
        return _empty_h2h()

    total = len(meetings)
    home_wins = 0
    away_wins = 0
    draws = 0
    home_goals_total = 0
    away_goals_total = 0

    for _, row in meetings.iterrows():
        is_home = row["HomeTeam"] == home_team
        ftr = row.get("FTR", "")
        hg = int(row.get("FTHG", 0) or 0)
        ag = int(row.get("FTAG", 0) or 0)

        if is_home:
            home_goals_total += hg
            away_goals_total += ag
            if ftr == "H":
                home_wins += 1
            elif ftr == "D":
                draws += 1
            else:
                away_wins += 1
        else:
            # This meeting had our "home" team playing away
            home_goals_total += ag
            away_goals_total += hg
            if ftr == "A":
                home_wins += 1
            elif ftr == "D":
                draws += 1
            else:
                away_wins += 1

    return {
        "total_meetings": total,
        "home_team_wins": home_wins,
        "draws": draws,
        "away_team_wins": away_wins,
        "home_win_rate": round(home_wins / total, 3),
        "draw_rate": round(draws / total, 3),
        "away_win_rate": round(away_wins / total, 3),
        "avg_home_goals": round(home_goals_total / total, 2),
        "avg_away_goals": round(away_goals_total / total, 2),
        # h2h_score: normalised 0–1 advantage for the home team in this fixture
        "h2h_score": round(home_wins / total, 3),
    }


def _empty_h2h() -> dict:
    return {
        "total_meetings": 0,
        "home_team_wins": 0,
        "draws": 0,
        "away_team_wins": 0,
        "home_win_rate": 0.33,
        "draw_rate": 0.33,
        "away_win_rate": 0.33,
        "avg_home_goals": 1.3,
        "avg_away_goals": 1.0,
        "h2h_score": 0.5,
    }
