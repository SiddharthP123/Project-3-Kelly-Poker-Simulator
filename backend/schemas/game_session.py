from datetime import datetime

from pydantic import Field, model_validator

from backend.schemas.base import ApiModel, OrmResponseModel


class CreateGameSessionRequest(ApiModel):
    # None means "use this user's own starting_bankroll default" (set at
    # signup) -- the first thing that field is actually used for.
    starting_bankroll: float | None = Field(default=None, gt=0)
    num_opponents: int = Field(ge=1, le=4)
    kelly_multiplier: float | None = Field(default=None, ge=0)
    small_blind: float = Field(default=1.0, gt=0)
    big_blind: float = Field(default=2.0, gt=0)

    @model_validator(mode='after')
    def check_big_blind_exceeds_small_blind(self):
        if self.big_blind <= self.small_blind:
            raise ValueError('big_blind must be greater than small_blind')
        return self


class GameSessionOpponentResponse(OrmResponseModel):
    seat_index: int
    persona: str


class GameSessionResponse(OrmResponseModel):
    id: int
    starting_bankroll: float
    current_bankroll: float
    kelly_multiplier: float | None
    status: str
    num_opponents: int
    small_blind: float
    big_blind: float
    started_at: datetime
    ended_at: datetime | None
    opponents: list[GameSessionOpponentResponse]


class BankrollHistoryPoint(OrmResponseModel):
    bankroll_after: float
    logged_at: datetime
