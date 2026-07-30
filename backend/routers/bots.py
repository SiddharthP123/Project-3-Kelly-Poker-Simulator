from fastapi import APIRouter, HTTPException, Request, Response

from backend.rate_limit import READS_LIMIT, limiter
from backend.schemas.bot import BotDecideRequest, BotDecideResponse
from backend.services.card_parsing import parse_cards
from backend.services.game_engine import PERSONAS

router = APIRouter(tags=['bots'])


@router.post('/bots/decide', response_model=BotDecideResponse)
@limiter.limit(READS_LIMIT)
def bot_decide(request: Request, response: Response, body: BotDecideRequest):
    bot = PERSONAS[body.persona]()
    hole_cards = parse_cards(body.hole_cards)
    board = tuple(parse_cards(body.board))

    try:
        action = bot.decide_from_hand(
            hole_cards, board, body.pot_size, body.bet_to_call,
            num_opponents=body.num_opponents, bankroll=body.bankroll,
            num_simulations=body.num_simulations, seed=body.seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return BotDecideResponse(action=action.action, raise_amount=action.raise_amount)
