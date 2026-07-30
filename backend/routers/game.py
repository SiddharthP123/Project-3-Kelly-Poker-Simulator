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
from backend.schemas.hand_history import HandHistoryResponse, PlayHandRequest
from backend.security import get_current_user
from backend.services.game_engine import play_hand

router = APIRouter(prefix='/game/sessions', tags=['game'])


def _get_owned_session_or_404(session_id: int, current_user: User, db: Session) -> GameSession:
    """A session that exists but belongs to someone else 404s exactly the
    same way as one that doesn't exist at all -- returning 403 there would
    confirm the session id is real, which is itself information leakage."""
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail='Game session not found')
    return session


# Every route below stacks two independent rate limits: the general
# IP-based bucket (READS_LIMIT/WRITES_LIMIT) plus USER_HOURLY_LIMIT keyed
# by the authenticated user's id -- see backend/rate_limit.py for why both
# layers matter. Both decorators are on the OUTER function; slowapi checks
# all stacked limits before the handler body runs, and a request is
# rejected if it exceeds any one of them.


@router.post('', response_model=GameSessionResponse)
@limiter.limit(WRITES_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def create_game_session(
    request: Request, response: Response, body: CreateGameSessionRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    starting_bankroll = body.starting_bankroll or current_user.starting_bankroll

    session = GameSession(
        user_id=current_user.id,
        starting_bankroll=starting_bankroll,
        current_bankroll=starting_bankroll,
        bot_persona=body.bot_persona,
        kelly_multiplier=body.kelly_multiplier,
    )
    db.add(session)
    db.flush()

    db.add(BankrollLog(game_session_id=session.id, bankroll_after=session.starting_bankroll))
    db.commit()
    db.refresh(session)

    return session


@router.get('/{session_id}', response_model=GameSessionResponse)
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def get_game_session(
    request: Request, response: Response, session_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return _get_owned_session_or_404(session_id, current_user, db)


@router.post('/{session_id}/hands', response_model=HandHistoryResponse)
@limiter.limit(WRITES_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def play_next_hand(
    request: Request, response: Response, session_id: int, body: PlayHandRequest = PlayHandRequest(),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    session = _get_owned_session_or_404(session_id, current_user, db)
    if session.status != 'active':
        raise HTTPException(status_code=400, detail='Game session has already ended')

    return play_hand(session, db, num_simulations=body.num_simulations, seed=body.seed)


@router.get('/{session_id}/hands', response_model=list[HandHistoryResponse])
@limiter.limit(READS_LIMIT)
@limiter.limit(USER_HOURLY_LIMIT, key_func=user_id_or_ip_key)
def list_hand_history(
    request: Request, response: Response, session_id: int, limit: int = 50, offset: int = 0,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _get_owned_session_or_404(session_id, current_user, db)
    return (
        db.query(HandHistory)
        .filter_by(game_session_id=session_id)
        .order_by(HandHistory.hand_number)
        .offset(offset)
        .limit(limit)
        .all()
    )


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
