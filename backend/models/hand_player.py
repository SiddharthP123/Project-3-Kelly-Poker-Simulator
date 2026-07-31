"""SQLAlchemy model for one seat's state in one hand -- hero or an
opponent, replacing the old singular hero_hole_cards/opponent_hole_cards
columns on HandHistory, which structurally can't hold 1-4 opponents.

Redaction changes with this table: unlike Part 10's dealt_*/hidden-column
pattern, hole_cards here is ALWAYS the real cards, for every seat, from
the moment the hand is dealt. A folded (or otherwise not-yet-earned)
seat's cards are hidden by never serializing this column in the response
schema for that seat -- not by leaving the column empty until showdown.
That's a deliberate mechanism change (Part 12 plan): it doesn't scale to
redact via storage for 5 seats x 4 streets the way a single hidden column
did for 2 seats x 1 decision.
"""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class HandPlayer(Base):
    __tablename__ = 'hand_players'
    __table_args__ = (UniqueConstraint('hand_history_id', 'seat_index'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    hand_history_id: Mapped[int] = mapped_column(
        ForeignKey('hand_histories.id'), index=True, nullable=False
    )
    seat_index: Mapped[int] = mapped_column(Integer, nullable=False)  # hero is always seat 0
    is_hero: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    persona: Mapped[str | None] = mapped_column(String(50), nullable=True)  # null for the hero seat

    starting_stack: Mapped[float] = mapped_column(Float, nullable=False)
    hole_cards: Mapped[str] = mapped_column(String(10), nullable=False)  # always real, see docstring

    folded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    all_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Populated once the hand resolves; null while it's still in progress.
    final_stack: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_result: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    hand_history: Mapped['HandHistory'] = relationship(back_populates='players')
