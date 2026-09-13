from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.rate_limit import READS_LIMIT, limiter
from backend.schemas.user_stats import UserStatsResponse
from backend.security import get_current_user
from backend.services.user_stats import compute_user_stats

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me/stats', response_model=UserStatsResponse)
@limiter.limit(READS_LIMIT)
def get_my_stats(
    request: Request, response: Response,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return compute_user_stats(current_user, db)
