"""SQLAlchemy model for one played hand.

Card fields are stored as comma-joined standard notation (e.g. "Ah,Ac"),
matching Card.from_str/str(card) exactly (poker/cards.py) -- no bespoke
serialisation format invented. opponent_hole_cards is only populated at
showdown; a folded opponent's cards are never known/stored, same as real
poker never reveals a folded hand.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class HandHistory(Base):
    __tablename__ = 'hand_histories'

    id: Mapped[int] = mapped_column(primary_key=True)
    game_session_id: Mapped[int] = mapped_column(
        ForeignKey('game_sessions.id'), index=True, nullable=False
    )
    hand_number: Mapped[int] = mapped_column(Integer, nullable=False)

    hero_hole_cards: Mapped[str] = mapped_column(String(10), nullable=False)
    board_cards: Mapped[str | None] = mapped_column(String(20), nullable=True)
    opponent_hole_cards: Mapped[str | None] = mapped_column(String(10), nullable=True)

    pot_size: Mapped[float] = mapped_column(Float, nullable=False)
    hero_action: Mapped[str] = mapped_column(String(10), nullable=False)
    bot_action: Mapped[str | None] = mapped_column(String(10), nullable=True)

    equity_at_decision: Mapped[float | None] = mapped_column(Float, nullable=True)
    kelly_recommended_stake: Mapped[float | None] = mapped_column(Float, nullable=True)

    winner: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hero_bankroll_delta: Mapped[float] = mapped_column(Float, nullable=False)

    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    game_session: Mapped['GameSession'] = relationship(back_populates='hands')
    bankroll_logs: Mapped[list['BankrollLog']] = relationship(back_populates='hand_history')
