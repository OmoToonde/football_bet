"""
Scrapes xG data from understat.com — no API key required.
Uses public HTML + embedded JSON data.
"""
import re
import json
import requests
from bs4 import BeautifulSoup

LEAGUE_MAP = {
    "premier-league": "EPL",
    "la-liga":        "La_liga",
    "serie-a":        "Serie_A",
    "bundesliga":     "Bundesliga",
    "ligue-1":        "Ligue_1",
    "eredivisie":     "RFPL",  # closest available; Eredivisie not on understat
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _extract_json_var(html: str, var_name: str) -> list | dict | None:
    """Extract a JSON variable embedded in Understat's page scripts."""
    pattern = rf"var\s+{var_name}\s*=\s*JSON\.parse\('(.+?)'\)"
    match = re.search(pattern, html)
    if not match:
        return None
    raw = match.group(1).encode("utf-8").decode("unicode_escape")
    return json.loads(raw)


def fetch_league_xg(league_slug: str, season: str = "2024") -> list[dict]:
    """
    Fetch all match xG values for a league/season.
    Returns list of dicts: {home, away, xg_home, xg_away, date, result}
    """
    league_code = LEAGUE_MAP.get(league_slug)
    if not league_code:
        return []

    url = f"https://understat.com/league/{league_code}/{season}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    data = _extract_json_var(resp.text, "datesData")
    if not data:
        return []

    matches = []
    for match in data:
        try:
            matches.append({
                "home_team": match["h"]["title"],
                "away_team": match["a"]["title"],
                "xg_home": float(match.get("xG", {}).get("h", 0) or 0),
                "xg_away": float(match.get("xG", {}).get("a", 0) or 0),
                "date": match.get("datetime", ""),
                "home_goals": int(match.get("goals", {}).get("h", 0) or 0),
                "away_goals": int(match.get("goals", {}).get("a", 0) or 0),
            })
        except (KeyError, TypeError, ValueError):
            continue

    return matches


def get_team_xg_stats(league_slug: str, team_name: str, season: str = "2024") -> dict:
    """Return average xG for and against for a team this season."""
    matches = fetch_league_xg(league_slug, season)
    home = [m for m in matches if m["home_team"] == team_name]
    away = [m for m in matches if m["away_team"] == team_name]

    def avg(lst, key):
        return round(sum(x[key] for x in lst) / len(lst), 2) if lst else 0.0

    return {
        "xg_for_home":     avg(home, "xg_home"),
        "xg_against_home": avg(home, "xg_away"),
        "xg_for_away":     avg(away, "xg_away"),
        "xg_against_away": avg(away, "xg_home"),
        "xg_for_avg":      round((avg(home, "xg_home") + avg(away, "xg_away")) / 2, 2),
        "xg_against_avg":  round((avg(home, "xg_away") + avg(away, "xg_home")) / 2, 2),
    }
