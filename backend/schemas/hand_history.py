from datetime import datetime

from pydantic import Field

from backend.schemas.base import ApiModel, OrmResponseModel


class HandHistoryResponse(OrmResponseModel):
    id: int
    hand_number: int
    hero_hole_cards: str
    board_cards: str | None
    opponent_hole_cards: str | None
    pot_size: float
    hero_action: str
    bot_action: str | None
    equity_at_decision: float | None
    kelly_recommended_stake: float | None
    winner: str | None
    hero_bankroll_delta: float
    played_at: datetime


class PlayHandRequest(ApiModel):
    num_simulations: int = Field(default=2000, ge=100, le=20000)
    seed: int | None = None
