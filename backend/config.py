from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Football Betting Intelligence"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./football_bet.db"

    # Data sources — all free, no API keys required
    football_data_base_url: str = "https://www.football-data.co.uk"
    understat_base_url: str = "https://understat.com"
    thesportsdb_base_url: str = "https://www.thesportsdb.com/api/v1/json/3"  # free public key

    # Freshness thresholds (seconds)
    pre_match_stale_threshold: int = 3600       # 1 hour
    live_score_stale_threshold: int = 10
    live_odds_stale_threshold: int = 15
    live_stats_stale_threshold: int = 30

    # Prediction engine weights (pre-match MVP)
    weight_recent_form: float = 0.15
    weight_home_away: float = 0.15
    weight_xg: float = 0.20
    weight_attacking: float = 0.10
    weight_defensive: float = 0.10
    weight_player_availability: float = 0.15
    weight_fixture_congestion: float = 0.05
    weight_h2h: float = 0.03
    weight_odds_movement: float = 0.07

    class Config:
        env_file = ".env"


settings = Settings()
