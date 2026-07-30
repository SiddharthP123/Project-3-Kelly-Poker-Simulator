from fastapi import APIRouter, HTTPException, Request, Response

from backend.rate_limit import READS_LIMIT, limiter
from backend.schemas.hand_evaluator import (
    BestHandRequest,
    BestHandResponse,
    CompareHandsRequest,
    CompareHandsResponse,
)
from backend.services.card_parsing import parse_cards
from poker.hand_evaluator import best_hand, compare_hands

router = APIRouter(tags=['hand-evaluator'])


@router.post('/hand-evaluator/best-hand', response_model=BestHandResponse)
@limiter.limit(READS_LIMIT)
def compute_best_hand(request: Request, response: Response, body: BestHandRequest):
    cards = parse_cards(body.cards)

    try:
        result, best_five = best_hand(cards)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return BestHandResponse(
        category=str(result.category),
        tiebreakers=[str(rank) for rank in result.tiebreakers],
        best_five=[str(card) for card in best_five],
    )


@router.post('/hand-evaluator/compare', response_model=CompareHandsResponse)
@limiter.limit(READS_LIMIT)
def compute_compare_hands(request: Request, response: Response, body: CompareHandsRequest):
    hands = [parse_cards(hand) for hand in body.hands]

    try:
        winners = compare_hands(hands)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return CompareHandsResponse(winners=winners)
