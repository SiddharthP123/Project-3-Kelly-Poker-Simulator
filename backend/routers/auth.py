from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.rate_limit import AUTH_LIMIT, READS_LIMIT, limiter
from backend.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse
from backend.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix='/auth', tags=['auth'])

# One message for every login failure mode (unknown email OR wrong
# password) -- distinguishing them would let an attacker enumerate which
# emails have accounts.
_INVALID_CREDENTIALS_DETAIL = 'Invalid email or password'


@router.post('/signup', response_model=TokenResponse)
@limiter.limit(AUTH_LIMIT)
def signup(request: Request, body: SignupRequest, db: Session = Depends(get_db)):
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        starting_bankroll=body.starting_bankroll,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail='An account with this email already exists') from error

    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post('/login', response_model=TokenResponse)
@limiter.limit(AUTH_LIMIT)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email).first()

    if user is None or user.hashed_password is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail=_INVALID_CREDENTIALS_DETAIL)

    return TokenResponse(access_token=create_access_token(user.id))


@router.get('/me', response_model=UserResponse)
@limiter.limit(READS_LIMIT)
def get_me(request: Request, current_user: User = Depends(get_current_user)):
    return current_user
