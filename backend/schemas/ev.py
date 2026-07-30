from pydantic import Field

from backend.schemas.base import ApiModel


class EvRequest(ApiModel):
    equity: float = Field(ge=0, le=1)
    pot_size: float = Field(ge=0)
    bet_to_call: float = Field(gt=0)
    raise_amount: float | None = Field(default=None, gt=0)
    fold_probability: float | None = Field(default=None, ge=0, le=1)


class EvResponse(ApiModel):
    action: str
    evs: dict[str, float]
