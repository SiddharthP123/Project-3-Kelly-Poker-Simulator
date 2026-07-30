"""SQLAlchemy model for one continuous play session against a bot persona.

user_id is nullable because there's no auth yet (Part 9) -- a session isn't
tied to a real signed-up user until then. current_bankroll is the "live"
number that gets updated after every hand and is what a Part 10 dashboard
header reads directly, rather than recomputing it from hand history.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class GameSession(Base):
    __tablename__ = 'game_sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), index=True, nullable=True)

    starting_bankroll: Mapped[float] = mapped_column(Float, nullable=False)
    current_bankroll: Mapped[float] = mapped_column(Float, nullable=False)
    bot_persona: Mapped[str] = mapped_column(String(50), nullable=False)
    kelly_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='active', nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped['User | None'] = relationship(back_populates='game_sessions')
    hands: Mapped[list['HandHistory']] = relationship(
        back_populates='game_session', cascade='all, delete-orphan'
    )
    bankroll_logs: Mapped[list['BankrollLog']] = relationship(
        back_populates='game_session', cascade='all, delete-orphan'
    )
