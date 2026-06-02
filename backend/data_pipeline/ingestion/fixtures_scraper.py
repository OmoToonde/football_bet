"""
Fetches upcoming fixtures from TheSportsDB free public endpoint.
Uses built-in demo key "3" — no registration required.
Falls back gracefully if the request fails.
"""
import requests
from datetime import datetime

BASE = "https://www.thesportsdb.com/api/v1/json/3"

# TheSportsDB league IDs (free tier, no registration)
LEAGUE_IDS = {
    "premier-league":  4328,
    "la-liga":         4335,
    "serie-a":         4332,
    "bundesliga":      4331,
    "ligue-1":         4334,
    "eredivisie":      4337,
    "champions-league": 4480,
}

HEADERS = {"User-Agent": "FootballIntelligenceApp/0.1 (educational)"}


def fetch_next_fixtures(league_slug: str) -> list[dict]:
    """Return upcoming fixtures for a league as list of dicts."""
    league_id = LEAGUE_IDS.get(league_slug)
    if not league_id:
        return []

    try:
        url = f"{BASE}/eventsnextleague.php?id={league_id}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events") or []
    except Exception as e:
        print(f"  ! fixtures_scraper: could not fetch {league_slug}: {e}")
        return []

    fixtures = []
    for ev in events:
        try:
            kickoff_str = f"{ev['dateEvent']} {ev.get('strTime', '00:00:00')}"
            kickoff = datetime.strptime(kickoff_str.strip(), "%Y-%m-%d %H:%M:%S")
            fixtures.append({
                "home_team": ev["strHomeTeam"],
                "away_team": ev["strAwayTeam"],
                "kickoff_time": kickoff,
                "venue": ev.get("strVenue", ""),
                "external_id": ev.get("idEvent", ""),
            })
        except (KeyError, ValueError):
            continue

    return fixtures


def fetch_last_results(league_slug: str) -> list[dict]:
    """Return recent results for a league."""
    league_id = LEAGUE_IDS.get(league_slug)
    if not league_id:
        return []

    try:
        url = f"{BASE}/eventspastleague.php?id={league_id}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        events = resp.json().get("events") or []
    except Exception as e:
        print(f"  ! fixtures_scraper: could not fetch results for {league_slug}: {e}")
        return []

    results = []
    for ev in events:
        try:
            kickoff_str = f"{ev['dateEvent']} {ev.get('strTime', '00:00:00')}"
            kickoff = datetime.strptime(kickoff_str.strip(), "%Y-%m-%d %H:%M:%S")
            results.append({
                "home_team": ev["strHomeTeam"],
                "away_team": ev["strAwayTeam"],
                "kickoff_time": kickoff,
                "home_score": int(ev.get("intHomeScore") or 0),
                "away_score": int(ev.get("intAwayScore") or 0),
                "venue": ev.get("strVenue", ""),
            })
        except (KeyError, ValueError):
            continue

    return results
