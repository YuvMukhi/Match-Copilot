from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str] = mapped_column(String(32), nullable=False)
    team1: Mapped[str] = mapped_column(String(64), nullable=False)
    team2: Mapped[str] = mapped_column(String(64), nullable=False)
    venue: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="in_progress")
    current_innings: Mapped[int] = mapped_column(Integer, default=1)
    total_overs: Mapped[int] = mapped_column(Integer, default=20)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    deliveries: Mapped[List["Delivery"]] = relationship("Delivery", back_populates="match", cascade="all, delete-orphan")
    chat_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="match", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    team: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # BAT, BOWL, AR, WK
    credits: Mapped[float] = mapped_column(Float, default=8.5)

    fantasy_team_associations: Mapped[List["FantasyTeamPlayer"]] = relationship(
        "FantasyTeamPlayer", back_populates="player"
    )


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(64), ForeignKey("matches.id"), index=True, nullable=False)
    innings: Mapped[int] = mapped_column(Integer, nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 1 to 20
    ball_in_over: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 6 (or more for extras)

    bowler_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), nullable=False)
    batter_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), nullable=False)
    non_striker_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), nullable=False)

    runs_batter: Mapped[int] = mapped_column(Integer, default=0)
    runs_extras: Mapped[int] = mapped_column(Integer, default=0)
    extra_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # wide, noball, bye, legbye

    is_wicket: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissal_kind: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # bowled, caught, lbw, run out, stumped
    dismissed_player_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("players.id"), nullable=True)
    fielder_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("players.id"), nullable=True)

    match: Mapped["Match"] = relationship("Match", back_populates="deliveries")
    bowler: Mapped["Player"] = relationship("Player", foreign_keys=[bowler_id])
    batter: Mapped["Player"] = relationship("Player", foreign_keys=[batter_id])
    dismissed_player: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[dismissed_player_id])
    fielder: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[fielder_id])


class FantasyTeam(Base):
    __tablename__ = "fantasy_teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    user_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    players: Mapped[List["FantasyTeamPlayer"]] = relationship(
        "FantasyTeamPlayer", back_populates="team", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="team", cascade="all, delete-orphan"
    )


class FantasyTeamPlayer(Base):
    __tablename__ = "fantasy_team_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(String(64), ForeignKey("fantasy_teams.id"), index=True, nullable=False)
    player_id: Mapped[str] = mapped_column(String(64), ForeignKey("players.id"), nullable=False)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vice_captain: Mapped[bool] = mapped_column(Boolean, default=False)

    team: Mapped["FantasyTeam"] = relationship("FantasyTeam", back_populates="players")
    player: Mapped["Player"] = relationship("Player", back_populates="fantasy_team_associations")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(64), ForeignKey("matches.id"), index=True, nullable=False)
    team_id: Mapped[str] = mapped_column(String(64), ForeignKey("fantasy_teams.id"), index=True, nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    match: Mapped["Match"] = relationship("Match", back_populates="chat_messages")
    team: Mapped["FantasyTeam"] = relationship("FantasyTeam", back_populates="chat_messages")
