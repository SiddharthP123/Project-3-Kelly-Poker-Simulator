"""SQLAlchemy model for an append-only bankroll time series.

Kept separate from HandHistory specifically so a Part-6-style growth chart
is a plain `SELECT ... ORDER BY logged_at` -- no aggregation over hand
history needed every time a dashboard loads. hand_history_id is nullable
because the very first row (session start) has no hand attached to it.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class BankrollLog(Base):
    __tablename__ = 'bankroll_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    game_session_id: Mapped[int] = mapped_column(
        ForeignKey('game_sessions.id'), index=True, nullable=False
    )
    hand_history_id: Mapped[int | None] = mapped_column(
        ForeignKey('hand_histories.id'), index=True, nullable=True
    )
    bankroll_after: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    game_session: Mapped['GameSession'] = relationship(back_populates='bankroll_logs')
    hand_history: Mapped['HandHistory | None'] = relationship(back_populates='bankroll_logs')
