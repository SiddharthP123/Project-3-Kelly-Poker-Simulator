from pydantic import Field

from backend.schemas.base import ApiModel


class KellyFromOddsRequest(ApiModel):
    win_probability: float = Field(ge=0, le=1)
    odds: float = Field(gt=0)
    fraction: float = Field(default=1.0, ge=0)


class KellyFromPotOddsRequest(ApiModel):
    equity: float = Field(ge=0, le=1)
    pot_size: float = Field(ge=0)
    bet_to_call: float = Field(gt=0)
    kelly_multiplier: float = Field(default=1.0, ge=0)


class KellyResponse(ApiModel):
    stake_fraction: float
