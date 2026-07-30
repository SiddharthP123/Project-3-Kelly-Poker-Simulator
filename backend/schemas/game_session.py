from datetime import datetime
from typing import Literal

from pydantic import Field

from backend.schemas.base import ApiModel, OrmResponseModel

BotPersona = Literal['tight-aggressive', 'loose-passive', 'random', 'kelly-optimal']


class CreateGameSessionRequest(ApiModel):
    starting_bankroll: float = Field(default=1000.0, gt=0)
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
