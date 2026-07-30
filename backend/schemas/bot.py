from typing import Literal

from pydantic import Field

from backend.schemas.base import ApiModel
from backend.schemas.card import CardStr


class BotDecideRequest(ApiModel):
    persona: Literal['tight-aggressive', 'loose-passive', 'random', 'kelly-optimal']
    hole_cards: list[CardStr] = Field(min_length=2, max_length=2)
    board: list[CardStr] = Field(default_factory=list)
    pot_size: float = Field(ge=0)
    bet_to_call: float = Field(gt=0)
    num_opponents: int = Field(default=1, ge=1, le=9)
    bankroll: float | None = Field(default=None, gt=0)
    # Seeds the equity Monte Carlo simulation for reproducibility. Has no
    # effect on 'random' persona's own action choice, which is separately
    # (and intentionally) equity-blind.
    num_simulations: int = Field(default=2000, ge=100, le=20000)
    seed: int | None = None


class BotDecideResponse(ApiModel):
    action: str
    raise_amount: float
