"""SQLAlchemy model for a registered user.

Deliberately minimal in Part 8 -- there's no signup/login flow yet (that's
Part 9's job) -- but the columns Part 9 needs already exist here, so
adding auth later is "add logic to existing rows," not "add columns to a
live table."
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Part 13 Phase 3 -- profile page. avatar_url is a pasted image URL, not
    # a real upload (this project has no file/object storage set up); a
    # bad/missing value just falls back to an initials circle client-side,
    # nothing enforced server-side. Both nullable -- an existing live row
    # just gets NULL until its owner fills the profile in.
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    starting_bankroll: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    game_sessions: Mapped[list['GameSession']] = relationship(back_populates='user')
