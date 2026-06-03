"""
API integration tests — Milestone 8
Spins up the FastAPI app in-process with an isolated SQLite DB and
exercises the public endpoints end-to-end.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient

# Use an in-memory-ish test DB file so we don't touch the real one
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_football_bet.db"

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    # Cleanup test DB
    try:
        os.remove("./test_football_bet.db")
    except OSError:
        pass


class TestPublicEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "running"

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_leagues_list(self, client):
        r = client.get("/leagues/")
        assert r.status_code == 200
        assert "leagues" in r.json()

    def test_matches_today(self, client):
        r = client.get("/matches/today")
        assert r.status_code == 200
        assert "matches" in r.json()

    def test_matches_live(self, client):
        r = client.get("/matches/live")
        assert r.status_code == 200
        assert isinstance(r.json()["matches"], list)

    def test_missing_match_returns_404(self, client):
        r = client.get("/matches/999999")
        assert r.status_code == 404


class TestPerformanceEndpoints:
    def test_overview(self, client):
        r = client.get("/performance/overview")
        assert r.status_code == 200

    def test_by_league(self, client):
        r = client.get("/performance/by-league")
        assert r.status_code == 200
        assert "leagues" in r.json()

    def test_roi(self, client):
        r = client.get("/performance/roi")
        assert r.status_code == 200
        assert "all_bets" in r.json()

    def test_data_health(self, client):
        r = client.get("/admin/data-health")
        assert r.status_code == 200
        assert "matches" in r.json()


class TestChampionsLeagueEndpoints:
    def test_cl_teams(self, client):
        r = client.get("/cl/teams")
        assert r.status_code == 200
        assert len(r.json()["teams"]) > 0

    def test_cl_match_prediction(self, client):
        r = client.post("/cl/match-prediction", json={
            "home_team": "Real Madrid", "home_strength": 0.92, "home_league": "la-liga",
            "away_team": "Ajax", "away_strength": 0.66, "away_league": "eredivisie",
        })
        assert r.status_code == 200
        body = r.json()
        total = body["home_win_probability"] + body["draw_probability"] + body["away_win_probability"]
        assert abs(total - 1.0) < 0.02
        # Real Madrid should be favoured
        assert body["home_win_probability"] > body["away_win_probability"]

    def test_cl_two_leg(self, client):
        r = client.post("/cl/two-leg-prediction", json={
            "home_team": "Arsenal", "home_strength": 0.82, "home_league": "premier-league",
            "away_team": "Porto", "away_strength": 0.70, "away_league": "primeira-liga",
            "first_leg_home_score": 2, "first_leg_away_score": 0,
        })
        assert r.status_code == 200
        body = r.json()
        # Arsenal up 2-0 should be heavy favourites
        assert body["home_qualify_probability"] > 0.7

    def test_cl_no_guaranteed_language(self, client):
        r = client.post("/cl/match-prediction", json={
            "home_team": "Bayern Munich", "home_strength": 0.89, "home_league": "bundesliga",
            "away_team": "Celtic", "away_strength": 0.60, "away_league": "premier-league",
        })
        text = r.json()["cross_league_note"].lower()
        for phrase in ["guaranteed win", "sure bet", "cannot lose"]:
            assert phrase not in text
