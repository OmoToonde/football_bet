"""
Team Badge Fetcher — pulls club crest image URLs from TheSportsDB.
Free public key "3" — no registration required.
"""
import requests
from difflib import SequenceMatcher

BASE = "https://www.thesportsdb.com/api/v1/json/3"

# Reuse the same league IDs as the fixtures scraper
LEAGUE_IDS = {
    "premier-league":   4328,
    "la-liga":          4335,
    "serie-a":          4332,
    "bundesliga":       4331,
    "ligue-1":          4334,
    "eredivisie":       4337,
    "champions-league": 4480,
}

HEADERS = {"User-Agent": "FootballIntelligenceApp/0.1 (educational)"}


def search_team_badge(team_name: str, expected_country: str | None = None) -> str | None:
    """
    Look up a single team's crest via TheSportsDB direct search.
    Far more reliable than fuzzy-matching within a league list.
    Returns a badge URL or None.
    """
    query = ALIASES.get(team_name.lower().strip(), team_name)
    try:
        url = f"{BASE}/searchteams.php?t={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        teams = resp.json().get("teams") or []
    except Exception:
        return None

    if not teams:
        return None

    # Prefer a soccer team, optionally in the expected country, with a badge
    best = None
    for t in teams:
        if (t.get("strSport") or "").lower() != "soccer":
            continue
        badge = t.get("strBadge") or t.get("strTeamBadge")
        if not badge:
            continue
        if expected_country and (t.get("strCountry") or "").lower() == expected_country.lower():
            return badge          # exact country match wins immediately
        if best is None:
            best = badge
    return best


def fetch_league_badges(league_slug: str) -> dict[str, str]:
    """
    Return {team_name: badge_url} for all teams in a league.
    """
    league_id = LEAGUE_IDS.get(league_slug)
    if not league_id:
        return {}

    try:
        url = f"{BASE}/lookup_all_teams.php?id={league_id}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        teams = resp.json().get("teams") or []
    except Exception as e:
        print(f"  ! team_badges: could not fetch {league_slug}: {e}")
        return {}

    badges: dict[str, str] = {}
    for t in teams:
        name = t.get("strTeam")
        badge = t.get("strBadge") or t.get("strTeamBadge")
        if name and badge:
            badges[name] = badge
    return badges


# Common abbreviations used by football-data.co.uk → canonical fragments
ALIASES = {
    "man city": "manchester city",
    "man united": "manchester united",
    "man utd": "manchester united",
    "nott'm forest": "nottingham forest",
    "wolves": "wolverhampton",
    "spurs": "tottenham",
    "ath bilbao": "athletic",
    "ath madrid": "atletico madrid",
    "atl madrid": "atletico madrid",
    "sociedad": "real sociedad",
    "betis": "real betis",
    "espanol": "espanyol",
    "vallecano": "rayo vallecano",
    "ein frankfurt": "eintracht frankfurt",
    "leverkusen": "bayer leverkusen",
    "m'gladbach": "monchengladbach",
    "dortmund": "borussia dortmund",
    "paris sg": "paris saint-germain",
    "psg": "paris saint-germain",
    "st etienne": "saint-etienne",
    "inter": "inter milan",
    "ac milan": "milan",
}


def _norm(name: str) -> str:
    """Normalise a club name for fuzzy matching (keep distinguishing tokens)."""
    n = name.lower().strip()
    n = ALIASES.get(n, n)
    for ch in [".", "'", "-", "&"]:
        n = n.replace(ch, " ")
    # strip generic suffixes only as standalone words
    drop = {"fc", "cf", "afc", "sc", "club", "de", "the", "1899", "1846", "05", "04"}
    words = [w for w in n.split() if w not in drop]
    return " ".join(words)


def best_match(target: str, candidates: list[str]) -> str | None:
    """
    Strict matcher — only returns a candidate we are confident about, to avoid
    assigning the wrong crest. Order of confidence:
      1. exact normalised match
      2. one name's tokens are a subset of the other's (e.g. "newcastle" ⊂ "newcastle united")
      3. very high sequence ratio (>= 0.88)
    Returns None (→ initials fallback) when uncertain.
    """
    t = _norm(target)
    tset = set(t.split())
    if not tset:
        return None

    exact = None
    subset_best, subset_score = None, 0.0
    ratio_best, ratio_score = None, 0.0

    for c in candidates:
        cn = _norm(c)
        cset = set(cn.split())
        if not cset:
            continue

        if t == cn:
            exact = c
            break

        # token subset in either direction, with a shared distinguishing word
        if tset <= cset or cset <= tset:
            inter = tset & cset
            # require the shorter side to be fully covered and non-trivial
            if inter and len(inter) >= min(len(tset), len(cset)):
                score = len(inter) / max(len(tset), len(cset))
                if score > subset_score:
                    subset_best, subset_score = c, score

        r = SequenceMatcher(None, t, cn).ratio()
        if r > ratio_score:
            ratio_best, ratio_score = c, r

    if exact:
        return exact
    if subset_best and subset_score >= 0.5:
        return subset_best
    if ratio_best and ratio_score >= 0.88:
        return ratio_best
    return None
