from datetime import datetime
from typing import List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship, Mapped


class Base(DeclarativeBase): ...


class Game(Base):
    """
    Represents a Secret Santa game

    Attributes:
        id: Game ID (primary key)
        game_code: Unique game code (e.g., SANTA42)
        creator_chat_id: Telegram chat ID of the creator
        is_locked: If True, no new participants can join
        is_drawn: If True, the draw has been done
        created_at: When the game was created
        auto_purge_at: When the game will be auto-deleted
        participants: List of participants
        draw_results: List of draw results
    """

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )
    creator_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_drawn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    auto_purge_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    participants: Mapped[List["Participant"]] = relationship(
        "Participant", back_populates="game", cascade="all, delete-orphan"
    )
    draw_results: Mapped[List["DrawResult"]] = relationship(
        "DrawResult", back_populates="game", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Game(id={self.id}, code='{self.game_code}', "
            f"locked={self.is_locked}, drawn={self.is_drawn})>"
        )


class Participant(Base):
    """
    Represents a participant in a Secret Santa game

    Attributes:
        id: Primary key
        game_id: Foreign key to Game
        name: Participant's display name (unique within game)
        joined_at: Timestamp when participant joined
        game: Related Game object
    """

    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="participants")

    __table_args__ = (
        UniqueConstraint("game_id", "name", name="uq_game_participant_name"),
    )

    def __repr__(self):
        return (
            f"<Participant(id={self.id}, name='{self.name}', game_id={self.game_id})>"
        )


class DrawResult(Base):
    """
    Represents a Secret Santa draw result

    Attributes:
        id: Primary key
        game_id: Foreign key to Game
        giver_name: Name of the person who gives a gift
        receiver_name: Name of the person who receives a gift
        game: Related Game object
    """

    __tablename__ = "draw_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    giver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="draw_results")

    def __repr__(self):
        return (
            f"<DrawResult(id={self.id}, "
            f"giver='{self.giver_name}', receiver='{self.receiver_name}')>"
        )
