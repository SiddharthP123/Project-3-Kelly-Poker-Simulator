from fastapi import APIRouter, HTTPException, Request

from backend.rate_limit import READS_LIMIT, limiter
from backend.schemas.ev import EvRequest, EvResponse
from poker.ev import best_action

router = APIRouter(tags=['ev'])


@router.post('/ev', response_model=EvResponse)
@limiter.limit(READS_LIMIT)
def compute_best_action(request: Request, body: EvRequest):
    # best_action itself raises ValueError if only one of raise_amount /
    # fold_probability is given -- no need to duplicate that check here.
    try:
        decision = best_action(
            body.equity, body.pot_size, body.bet_to_call,
            raise_amount=body.raise_amount, fold_probability=body.fold_probability,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return EvResponse(action=decision.action, evs=decision.evs)
