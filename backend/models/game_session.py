"""SQLAlchemy model for one continuous play session against 1-4 bot
opponents (Part 12) -- previously a single fixed bot_persona (Parts 8-11).

user_id is nullable because there's no auth yet (Part 9) -- a session isn't
tied to a real signed-up user until then. current_bankroll is the "live"
number that gets updated after every hand and is what a Part 10 dashboard
header reads directly, rather than recomputing it from hand history.

bot_persona is vestigial as of Part 12 (kept NOT NULL with a placeholder
for new multi-opponent sessions rather than dropped/nullable-ed as part of
this schema change -- that cleanup is deferred to its own deliberate step,
per the Part 12 plan). Real per-seat personas now live in
`game_session_opponents`.

num_opponents/small_blind/big_blind are nullable because they don't exist
on rows created before Part 12 -- adding them to the live table is a
manual `ALTER TABLE` (not `create_all()`-safe), done separately; see
backend/migrations/README.md.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
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

    num_opponents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    small_blind: Mapped[float | None] = mapped_column(Float, nullable=True)
    big_blind: Mapped[float | None] = mapped_column(Float, nullable=True)

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
    opponents: Mapped[list['GameSessionOpponent']] = relationship(
        back_populates='game_session', cascade='all, delete-orphan'
    )
