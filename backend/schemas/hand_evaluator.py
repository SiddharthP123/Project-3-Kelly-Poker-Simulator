from typing import Annotated

from pydantic import Field

from backend.schemas.base import ApiModel
from backend.schemas.card import CardStr

# Each hand is 5-7 cards, same bound as BestHandRequest below -- applied
# per-hand here so a CompareHandsRequest can't smuggle in an oversized
# hand just because the outer list constraint only limits hand *count*.
_HandCards = Annotated[list[CardStr], Field(min_length=5, max_length=7)]


class BestHandRequest(ApiModel):
    cards: list[CardStr] = Field(min_length=5, max_length=7)


class BestHandResponse(ApiModel):
    category: str
    tiebreakers: list[str]
    best_five: list[str]


class CompareHandsRequest(ApiModel):
    # max_length=10 -- more than a real poker table ever seats -- caps the
    # number of hands compare_hands() has to evaluate per request.
    hands: list[_HandCards] = Field(min_length=2, max_length=10)


class CompareHandsResponse(ApiModel):
    winners: list[int]
