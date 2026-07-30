from pydantic import Field

from backend.schemas.base import ApiModel
from backend.schemas.card import CardStr


class BestHandRequest(ApiModel):
    cards: list[CardStr] = Field(min_length=5, max_length=7)


class BestHandResponse(ApiModel):
    category: str
    tiebreakers: list[str]
    best_five: list[str]


class CompareHandsRequest(ApiModel):
    hands: list[list[CardStr]] = Field(min_length=2)


class CompareHandsResponse(ApiModel):
    winners: list[int]
