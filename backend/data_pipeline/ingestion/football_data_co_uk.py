"""
Ingests historical match data + odds from football-data.co.uk
Completely free — no API key required, just CSV downloads.
"""
import io
import requests
import pandas as pd
from datetime import datetime

# Maps our league slugs to football-data.co.uk CSV paths
LEAGUE_CSV_URLS = {
    "premier-league":  "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
    "championship":    "https://www.football-data.co.uk/mmz4281/2526/E1.csv",
    "la-liga":         "https://www.football-data.co.uk/mmz4281/2526/SP1.csv",
    "serie-a":         "https://www.football-data.co.uk/mmz4281/2526/I1.csv",
    "bundesliga":      "https://www.football-data.co.uk/mmz4281/2526/D1.csv",
    "ligue-1":         "https://www.football-data.co.uk/mmz4281/2526/F1.csv",
    "eredivisie":      "https://www.football-data.co.uk/mmz4281/2526/N1.csv",
}

# Columns we care about
CORE_COLS = [
    "Date", "HomeTeam", "AwayTeam",
    "FTHG", "FTAG", "FTR",          # full-time goals + result
    "HS", "AS",                      # shots
    "HST", "AST",                    # shots on target
    "B365H", "B365D", "B365A",      # Bet365 odds H/D/A
]


def fetch_league_results(league_slug: str) -> pd.DataFrame:
    """Download and return recent results for a league as a DataFrame."""
    url = LEAGUE_CSV_URLS.get(league_slug)
    if not url:
        raise ValueError(f"Unknown league slug: {league_slug}")

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.text), usecols=lambda c: c in CORE_COLS)
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam"])
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df.sort_values("Date", ascending=False).reset_index(drop=True)


def compute_team_form(df: pd.DataFrame, team: str, last_n: int = 5) -> dict:
    """
    Compute recent form metrics for a team from historical results.
    Returns goals scored/conceded, win rate, xG proxies (shots on target ratio).
    """
    home_games = df[df["HomeTeam"] == team].copy()
    away_games = df[df["AwayTeam"] == team].copy()

    home_games["goals_for"] = home_games["FTHG"]
    home_games["goals_against"] = home_games["FTAG"]
    home_games["won"] = home_games["FTR"] == "H"

    away_games["goals_for"] = away_games["FTAG"]
    away_games["goals_against"] = away_games["FTHG"]
    away_games["won"] = away_games["FTR"] == "A"

    all_games = (
        pd.concat([home_games, away_games])
        .sort_values("Date", ascending=False)
        .head(last_n)
    )

    if all_games.empty:
        return {}

    return {
        "games": len(all_games),
        "wins": int(all_games["won"].sum()),
        "goals_scored": float(all_games["goals_for"].mean()),
        "goals_conceded": float(all_games["goals_against"].mean()),
        "win_rate": float(all_games["won"].mean()),
    }


def compute_home_away_form(df: pd.DataFrame, team: str, last_n: int = 5) -> dict:
    """Separate home and away form metrics."""
    home = df[df["HomeTeam"] == team].head(last_n)
    away = df[df["AwayTeam"] == team].head(last_n)

    def _stats(games, goals_for_col, goals_against_col, win_result):
        if games.empty:
            return {"win_rate": 0.0, "goals_scored": 0.0, "goals_conceded": 0.0}
        return {
            "win_rate": float((games["FTR"] == win_result).mean()),
            "goals_scored": float(games[goals_for_col].mean()),
            "goals_conceded": float(games[goals_against_col].mean()),
        }

    return {
        "home": _stats(home, "FTHG", "FTAG", "H"),
        "away": _stats(away, "FTAG", "FTHG", "A"),
    }


def get_odds_for_match(df: pd.DataFrame, home_team: str, away_team: str) -> dict | None:
    """Get the most recent Bet365 odds for a specific match."""
    row = df[(df["HomeTeam"] == home_team) & (df["AwayTeam"] == away_team)]
    if row.empty:
        return None
    row = row.iloc[0]
    return {
        "home_odds": float(row.get("B365H", 0) or 0),
        "draw_odds": float(row.get("B365D", 0) or 0),
        "away_odds": float(row.get("B365A", 0) or 0),
    }
