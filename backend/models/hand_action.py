"""SQLAlchemy model for one action taken during a hand -- the replayable
log a future frontend animates through street by street, seat by seat,
even though a single API response can resolve several actions/streets at
once (e.g. hero calls all-in preflop and the rest of the hand runs itself).

action/amount deliberately reuse poker.betting.BettingAction's own
vocabulary ('post_blind'/'fold'/'match'/'raise_to', and the incremental
chip amount committed by that action) rather than inventing a second one.

equity_at_decision/kelly_recommended_stake are only ever set on hero's own
rows -- relocated here from HandHistory (which only had room for one
value per hand) now that a hero decision happens once per street, not
once per hand.
"""

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class HandAction(Base):
    __tablename__ = 'hand_actions'
    __table_args__ = (UniqueConstraint('hand_history_id', 'seq'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    hand_history_id: Mapped[int] = mapped_column(
        ForeignKey('hand_histories.id'), index=True, nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-based order across the whole hand
    street: Mapped[str] = mapped_column(String(10), nullable=False)
    seat_index: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # post_blind/fold/match/raise_to
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    pot_size_after: Mapped[float] = mapped_column(Float, nullable=False)

    equity_at_decision: Mapped[float | None] = mapped_column(Float, nullable=True)
    kelly_recommended_stake: Mapped[float | None] = mapped_column(Float, nullable=True)

    hand_history: Mapped['HandHistory'] = relationship(back_populates='actions')
