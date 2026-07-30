"""Password hashing and JWT issuing/validation.

Key insight: the API never stores or compares raw passwords -- only a
bcrypt hash. bcrypt is deliberately slow (it's a tunable "work factor"
hash, not a fast general-purpose hash like SHA-256), specifically so that
brute-forcing a stolen hash database is computationally expensive -- that
slowness is the entire point, not a performance bug to fix later.

JWTs are stateless: the server never stores issued tokens anywhere, it
just verifies the signature and expiry on each request. That's what makes
`get_current_user` a single fast dependency with no database round trip
needed to validate the token itself (only to load the user row it names).
"""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import User

logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {'sub': str(user_id), 'exp': expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _decode_user_id(token: str) -> int:
    """Returns the user id encoded in a valid, unexpired token.

    Raises one generic 401 for every failure mode (expired, malformed,
    wrong signature) -- deliberately not distinguishing which, so a caller
    can't use the error message to probe for what a valid token looks like.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload['sub'])
    except (jwt.PyJWTError, KeyError, ValueError) as error:
        # Security: log that a bad token was presented, but never the
        # token itself -- a leaked log is a much smaller problem if it
        # never contained anything an attacker could replay.
        logger.warning('Rejected invalid or expired access token: %s', type(error).__name__)
        raise HTTPException(status_code=401, detail='Invalid or expired token') from error


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = _decode_user_id(credentials.credentials)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    return user
