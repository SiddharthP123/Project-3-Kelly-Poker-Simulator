from fastapi import APIRouter, HTTPException, Request

from backend.rate_limit import READS_LIMIT, limiter
from backend.schemas.equity import EquityRequest, EquityResponse
from backend.services.card_parsing import parse_cards
from poker.equity import calculate_equity

router = APIRouter(tags=['equity'])


@router.post('/equity', response_model=EquityResponse)
@limiter.limit(READS_LIMIT)
def compute_equity(request: Request, body: EquityRequest):
    hole_cards = parse_cards(body.hole_cards)
    board = tuple(parse_cards(body.board))

    try:
        result = calculate_equity(
            hole_cards,
            num_opponents=body.num_opponents,
            board=board,
            num_simulations=body.num_simulations,
            seed=body.seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return EquityResponse(win=result.win, tie=result.tie, lose=result.lose, equity=result.equity)
