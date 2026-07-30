from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from backend.schemas.base import ApiModel, OrmResponseModel


class HandHistoryResponse(OrmResponseModel):
    id: int
    hand_number: int
    hero_hole_cards: str
    board_cards: str | None
    opponent_hole_cards: str | None
    pot_size: float
    # Not an ORM column -- the router sets this attribute on the HandHistory
    # instance right before returning it (see routers/game.py), since every
    # hand currently uses the same fixed DEFAULT_BET_TO_CALL. Exposed
    # explicitly so the frontend never has to hardcode a backend constant.
    bet_to_call: float
    hero_action: str | None
    bot_action: str | None
    equity_at_decision: float | None
    kelly_recommended_stake: float | None
    winner: str | None
    hero_bankroll_delta: float | None
    played_at: datetime


class DealHandRequest(ApiModel):
    num_simulations: int = Field(default=2000, ge=100, le=20000)
    seed: int | None = None


class ActRequest(ApiModel):
    action: Literal['fold', 'call', 'raise']
    raise_amount: float | None = Field(default=None, gt=0)
    num_simulations: int = Field(default=2000, ge=100, le=20000)
    seed: int | None = None

    @model_validator(mode='after')
    def check_raise_amount_matches_action(self):
        if self.action == 'raise' and self.raise_amount is None:
            raise ValueError('raise_amount is required when action is "raise"')
        if self.action != 'raise' and self.raise_amount is not None:
            raise ValueError('raise_amount must only be provided when action is "raise"')
        return self
