from fastapi import APIRouter, HTTPException, Request, Response

from backend.rate_limit import READS_LIMIT, limiter
from backend.schemas.kelly import KellyFromOddsRequest, KellyFromPotOddsRequest, KellyResponse
from poker.kelly import fractional_kelly, kelly_fraction_from_pot_odds

router = APIRouter(tags=['kelly'])


@router.post('/kelly/from-odds', response_model=KellyResponse)
@limiter.limit(READS_LIMIT)
def kelly_from_odds(request: Request, response: Response, body: KellyFromOddsRequest):
    try:
        fraction = fractional_kelly(body.win_probability, body.odds, body.fraction)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return KellyResponse(stake_fraction=fraction)


@router.post('/kelly/from-pot-odds', response_model=KellyResponse)
@limiter.limit(READS_LIMIT)
def kelly_from_pot_odds(request: Request, response: Response, body: KellyFromPotOddsRequest):
    try:
        fraction = kelly_fraction_from_pot_odds(
            body.equity, body.pot_size, body.bet_to_call, body.kelly_multiplier
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return KellyResponse(stake_fraction=fraction)
