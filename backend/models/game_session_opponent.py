"""SQLAlchemy model for one opponent seat's persona assignment, fixed for
the life of a game session.

Part 12 (Real Poker Engine) replaces the old single fixed `bot_persona`
per session with 1-4 opponents, each with their own persona sampled from
`poker.bots.assign_opponent_personas` at session-creation time and reused
every hand -- one row per opponent seat, rather than a single column that
can't hold more than one persona.
"""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class GameSessionOpponent(Base):
    __tablename__ = 'game_session_opponents'
    __table_args__ = (UniqueConstraint('game_session_id', 'seat_index'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_session_id: Mapped[int] = mapped_column(
        ForeignKey('game_sessions.id'), index=True, nullable=False
    )
    seat_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..4; hero is always seat 0
    persona: Mapped[str] = mapped_column(String(50), nullable=False)

    game_session: Mapped['GameSession'] = relationship(back_populates='opponents')
