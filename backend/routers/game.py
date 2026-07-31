from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BankrollLog, GameSession, HandHistory, User
from backend.rate_limit import READS_LIMIT, USER_HOURLY_LIMIT, WRITES_LIMIT, limiter, user_id_or_ip_key
from backend.schemas.game_session import (
    BankrollHistoryPoint,
    CreateGameSessionRequest,
    GameSessionResponse,
)
from backend.schemas.hand_history import ActRequest, DealHandRequest, HandResponse
from backend.security import get_current_user
from backend.services.game_engine import (
    act_on_hand,
    build_historical_response,
    create_game_session,
    deal_hand,
    get_pending_hand,
    get_pending_hand_response,
)

router = APIRouter(prefix='/game/sessions', tags=['game'])


def _get_owned_session_or_404(session_id: int, current_user: User, db: Session) -> GameSession:
    """A session that exists but belongs to someone else 404s exactly the
    same way as one that doesn't exist at all -- returning 403 there would
    confirm the session id is real, which is itself information leakage."""
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail='Game session not found')
    return session


def _get_owned_hand_or_404(session: GameSession, hand_id: int, db: Session) -> HandHistory:
    hand = db.get(HandHistory, hand_id)
    if hand is None or hand.game_session_id != session.id:
        raise HTTPException(status_code=404, detail='Hand not found')
    return hand


# Every route below stacks two independent rate limits: the general
# IP-based bucket (READS_LIMIT/WRITES_LIMIT) plus USER_HOURLY_LIMIT keyed
# by the authenticated user's id -- see backend/rate_limit.py for why both
# layers matter. Both decorators are on the OUTER function; slowapi checks
# all stacked limits before the handler body runs, and a request is
# rejected if it exceeds any one of them.


@router.post('', response_model=GameSessionResponse)
@limiter.limit(WRITES_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def create_session(
    request: Request, response: Response, body: CreateGameSessionRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return create_game_session(current_user, body, db)


@router.get('/{session_id}', response_model=GameSessionResponse)
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def get_game_session(
    request: Request, response: Response, session_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return _get_owned_session_or_404(session_id, current_user, db)


@router.post('/{session_id}/hands/deal', response_model=HandResponse)
@limiter.limit(WRITES_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def deal_next_hand(
    request: Request, response: Response, session_id: int, body: DealHandRequest = DealHandRequest(),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    if session.status != 'active':
        raise HTTPException(status_code=400, detail='Game session has already ended')

    return deal_hand(session, db, seed=body.seed)


@router.get('/{session_id}/hands/pending', response_model=HandResponse)
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def get_pending_hand_route(
    request: Request, response: Response, session_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    hand = get_pending_hand(session, db)
    if hand is None:
        raise HTTPException(status_code=404, detail='No pending hand for this session')
    return get_pending_hand_response(hand, db)


@router.post('/{session_id}/hands/{hand_id}/act', response_model=HandResponse)
@limiter.limit(WRITES_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def act_on_hand_route(
    request: Request, response: Response, session_id: int, hand_id: int, body: ActRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    hand = _get_owned_hand_or_404(session, hand_id, db)
    if hand.street is None or hand.street == 'complete':
        raise HTTPException(status_code=400, detail='This hand has already been resolved')

    try:
        return act_on_hand(hand, body.action, body.raise_to, db)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get('/{session_id}/hands', response_model=list[HandResponse])
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def list_hand_history(
    request: Request, response: Response, session_id: int, limit: int = 50, offset: int = 0,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    hands = (
        db.query(HandHistory)
        .filter_by(game_session_id=session.id)
        .order_by(HandHistory.hand_number)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [build_historical_response(hand) for hand in hands]


@router.get('/{session_id}/hands/{hand_id}', response_model=HandResponse)
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def get_hand(
    request: Request, response: Response, session_id: int, hand_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    hand = _get_owned_hand_or_404(session, hand_id, db)
    return build_historical_response(hand)


@router.get('/{session_id}/bankroll-history', response_model=list[BankrollHistoryPoint])
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def get_bankroll_history(
    request: Request, response: Response, session_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _get_owned_session_or_404(session_id, current_user, db)
    return (
        db.query(BankrollLog)
        .filter_by(game_session_id=session_id)
        .order_by(BankrollLog.logged_at)
        .all()
    )


@router.post('/{session_id}/end', response_model=GameSessionResponse)
@limiter.limit(WRITES_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def end_game_session(
    request: Request, response: Response, session_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    session.status = 'ended'
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session
