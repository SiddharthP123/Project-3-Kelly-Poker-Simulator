from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from backend.schemas.base import ApiModel, OrmResponseModel


class HandPlayerResponse(OrmResponseModel):
    seat_index: int
    is_hero: bool
    persona: str | None
    stack: float  # current, live stack -- not HandPlayer.final_stack, which is only set at showdown
    # Redaction happens here, not in storage (HandPlayer.hole_cards is always
    # the real cards) -- null unless this seat has earned the right to be
    # seen: it's always visible for hero's own seat, and for every other
    # seat once the hand reaches a genuine multi-way showdown. A folded
    # seat's cards, or a fold-out winner's, are never revealed.
    hole_cards: str | None
    folded: bool
    all_in: bool
    is_winner: bool
    net_result: float | None


class LegalActionBoundsResponse(ApiModel):
    can_fold: bool
    can_check: bool
    can_call: bool
    call_amount: float
    can_raise: bool
    min_raise_to: float
    max_raise_to: float


class HandActionLogEntry(ApiModel):
    seq: int
    street: str
    seat_index: int
    action: str
    amount: float
    pot_size_after: float
    # Only ever non-null for hero's own action rows, and only once
    # persisted (Part 12 Phase 8) -- a fresh, not-yet-persisted action in
    # a live response's `actions` list (see HandResponse) doesn't carry
    # these; they're populated here only when reading already-recorded
    # history (build_historical_response), one value per street instead
    # of the single once-per-hand value Parts 8-10 stored.
    equity_at_decision: float | None = None
    kelly_recommended_stake: float | None = None


class HandResponse(OrmResponseModel):
    id: int
    hand_number: int
    button_seat: int
    street: str  # 'preflop' | 'flop' | 'turn' | 'river' | 'complete'
    board_cards: str | None
    pot_size: float
    players: list[HandPlayerResponse]
    # Only present when it's genuinely hero's turn to act (street != 'complete').
    legal_action_bounds: LegalActionBoundsResponse | None
    # Hero's equity/Kelly-recommended stake for the CURRENT decision --
    # both null once street == 'complete'; kelly_recommended_stake is
    # additionally null whenever hero can check for free (nothing to
    # call), since Kelly sizing needs a real bet size to anchor to (see
    # poker.kelly.kelly_fraction_from_pot_odds, which requires
    # bet_to_call > 0 -- the same scope Part 5 originally established).
    equity_at_decision: float | None
    kelly_recommended_stake: float | None
    # Only the actions new since the last response (deal returns everything
    # since dealing; act returns whatever this specific request resolved) --
    # not the whole hand's history repeated every time, so a frontend can
    # animate incrementally through them.
    actions: list[HandActionLogEntry]
    winners: list[int] | None
    played_at: datetime


class DealHandRequest(ApiModel):
    seed: int | None = None


class ActRequest(ApiModel):
    action: Literal['fold', 'call', 'raise']
    # The desired absolute committed_street total for this street (matching
    # poker.hand_flow.apply_hero_action's own raise_to parameter) -- not an
    # incremental amount on top of whatever's already committed.
    raise_to: float | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def check_raise_to_matches_action(self):
        if self.action == 'raise' and self.raise_to is None:
            raise ValueError('raise_to is required when action is "raise"')
        if self.action != 'raise' and self.raise_to is not None:
            raise ValueError('raise_to must only be provided when action is "raise"')
        return self
