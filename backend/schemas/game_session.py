from datetime import datetime
from typing import Literal

from pydantic import Field

from backend.schemas.base import ApiModel, OrmResponseModel

BotPersona = Literal['tight-aggressive', 'loose-passive', 'random', 'kelly-optimal']


class CreateGameSessionRequest(ApiModel):
    # None means "use this user's own starting_bankroll default" (set at
    # signup) -- the first thing that field is actually used for.
    starting_bankroll: float | None = Field(default=None, gt=0)
    bot_persona: BotPersona
    kelly_multiplier: float | None = Field(default=None, ge=0)


class GameSessionResponse(OrmResponseModel):
    id: int
    starting_bankroll: float
    current_bankroll: float
    bot_persona: str
    kelly_multiplier: float | None
    status: str
    started_at: datetime
    ended_at: datetime | None


class BankrollHistoryPoint(OrmResponseModel):
    bankroll_after: float
    logged_at: datetime
