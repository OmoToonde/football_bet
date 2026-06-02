from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from backend.db.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"
    LIVE_HIGH_RISK = "Live High Risk"
    NO_BET = "No Bet Recommended"


class FreshnessStatus(str, enum.Enum):
    FRESH = "Fresh"
    ACCEPTABLE = "Acceptable"
    INCOMPLETE = "Incomplete"
    STALE = "Stale"
    BLOCKED = "Blocked"
    LIVE_DELAYED = "Live Delayed"


class PredictionMode(str, enum.Enum):
    PRE_MATCH = "pre_match"
    LIVE = "live"


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(50))
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    favourite_teams: Mapped[str | None] = mapped_column(Text)   # JSON list
    favourite_leagues: Mapped[str | None] = mapped_column(Text) # JSON list
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bets: Mapped[list["UserBet"]] = relationship(back_populates="user")


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(50))   # domestic / european
    season: Mapped[str] = mapped_column(String(10))
    slug: Mapped[str] = mapped_column(String(50), unique=True)  # e.g. "premier-league"

    teams: Mapped[list["Team"]] = relationship(back_populates="league")
    matches: Mapped[list["Match"]] = relationship(back_populates="league")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    league_id: Mapped[int | None] = mapped_column(ForeignKey("leagues.id"))
    logo_url: Mapped[str | None] = mapped_column(String(500))

    league: Mapped["League | None"] = relationship(back_populates="teams")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    kickoff_time: Mapped[datetime] = mapped_column(DateTime)
    venue: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), default=MatchStatus.SCHEDULED
    )
    final_home_score: Mapped[int | None] = mapped_column(Integer)
    final_away_score: Mapped[int | None] = mapped_column(Integer)

    league: Mapped["League"] = relationship(back_populates="matches")
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])
    snapshots: Mapped[list["MatchDataSnapshot"]] = relationship(back_populates="match")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="match")
    live_states: Mapped[list["LiveMatchState"]] = relationship(back_populates="match")


class MatchDataSnapshot(Base):
    __tablename__ = "match_data_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    odds_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    injury_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    lineup_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    stats_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    freshness_status: Mapped[FreshnessStatus] = mapped_column(
        Enum(FreshnessStatus), default=FreshnessStatus.ACCEPTABLE
    )
    raw_data: Mapped[str | None] = mapped_column(Text)  # JSON blob

    match: Mapped["Match"] = relationship(back_populates="snapshots")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    data_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("match_data_snapshots.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    mode: Mapped[PredictionMode] = mapped_column(Enum(PredictionMode))
    recommended_bet: Mapped[str] = mapped_column(String(100))
    expected_score: Mapped[str | None] = mapped_column(String(20))     # e.g. "2-1"
    home_win_probability: Mapped[float | None] = mapped_column(Float)
    draw_probability: Mapped[float | None] = mapped_column(Float)
    away_win_probability: Mapped[float | None] = mapped_column(Float)
    home_xg: Mapped[float | None] = mapped_column(Float)
    away_xg: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel))
    value_rating: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(Text)
    data_freshness_status: Mapped[FreshnessStatus] = mapped_column(Enum(FreshnessStatus))
    lineups_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    prediction_status: Mapped[str] = mapped_column(String(50), default="active")

    match: Mapped["Match"] = relationship(back_populates="predictions")
    scorelines: Mapped[list["ScorelineProbability"]] = relationship(back_populates="prediction")
    evaluation: Mapped["PredictionEvaluation | None"] = relationship(back_populates="prediction")


class ScorelineProbability(Base):
    __tablename__ = "scoreline_probabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"))
    home_goals: Mapped[int] = mapped_column(Integer)
    away_goals: Mapped[int] = mapped_column(Integer)
    probability: Mapped[float] = mapped_column(Float)

    prediction: Mapped["Prediction"] = relationship(back_populates="scorelines")


class LiveMatchState(Base):
    __tablename__ = "live_match_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    match_minute: Mapped[int | None] = mapped_column(Integer)
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    red_cards_home: Mapped[int] = mapped_column(Integer, default=0)
    red_cards_away: Mapped[int] = mapped_column(Integer, default=0)
    substitutions_home: Mapped[int] = mapped_column(Integer, default=0)
    substitutions_away: Mapped[int] = mapped_column(Integer, default=0)
    live_xg_home: Mapped[float | None] = mapped_column(Float)
    live_xg_away: Mapped[float | None] = mapped_column(Float)
    live_odds_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    event_feed_freshness: Mapped[FreshnessStatus] = mapped_column(
        Enum(FreshnessStatus), default=FreshnessStatus.ACCEPTABLE
    )

    match: Mapped["Match"] = relationship(back_populates="live_states")


class PredictionEvaluation(Base):
    __tablename__ = "prediction_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), unique=True)
    actual_home_score: Mapped[int | None] = mapped_column(Integer)
    actual_away_score: Mapped[int | None] = mapped_column(Integer)
    winner_correct: Mapped[bool | None] = mapped_column(Boolean)
    exact_score_correct: Mapped[bool | None] = mapped_column(Boolean)
    goal_margin_error: Mapped[float | None] = mapped_column(Float)
    bet_result: Mapped[str | None] = mapped_column(String(20))  # win / loss / void
    profit_loss_result: Mapped[float | None] = mapped_column(Float)
    evaluation_notes: Mapped[str | None] = mapped_column(Text)

    prediction: Mapped["Prediction"] = relationship(back_populates="evaluation")


class UserBet(Base):
    __tablename__ = "user_bets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    prediction_id: Mapped[int | None] = mapped_column(ForeignKey("predictions.id"))
    bet_type: Mapped[str] = mapped_column(String(100))
    selection: Mapped[str] = mapped_column(String(200))
    odds: Mapped[float] = mapped_column(Float)
    stake: Mapped[float] = mapped_column(Float)
    result: Mapped[str | None] = mapped_column(String(20))
    profit_loss: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="bets")
