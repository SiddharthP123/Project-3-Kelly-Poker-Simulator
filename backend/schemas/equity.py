from pydantic import Field

from backend.schemas.base import ApiModel
from backend.schemas.card import CardStr


class EquityRequest(ApiModel):
    hole_cards: list[CardStr] = Field(min_length=2, max_length=2)
    # A board is never more than 5 community cards -- capped here (rather
    # than relying only on calculate_equity's own ValueError) so an
    # oversized list is rejected before any per-card validation work runs.
    board: list[CardStr] = Field(default_factory=list, max_length=5)
    num_opponents: int = Field(default=1, ge=1, le=9)
    # Capped well below what would let this endpoint be used as a
    # CPU-exhaustion vector (each simulation runs a full hand evaluation).
    num_simulations: int = Field(default=10000, ge=100, le=20000)
    seed: int | None = None


class EquityResponse(ApiModel):
    win: float
    tie: float
    lose: float
    equity: float
