"""FastAPI application entrypoint.

Run locally with:
    uvicorn backend.main:app --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings
from backend.middleware import SecurityHeadersMiddleware
from backend.rate_limit import limiter
from backend.routers import auth, bots, equity, ev, game, hand_evaluator, health, kelly

# Basic stdout logging so the security-event log calls throughout backend/
# (failed logins, rejected tokens, rate limit hits) actually go somewhere
# visible when running the server -- no external logging service needed
# for a project at this stage.
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title='Kelly Poker Simulator API')
app.state.limiter = limiter


def _log_and_handle_rate_limit(request: Request, exc: RateLimitExceeded):
    logger.warning('Rate limit exceeded for ip=%s on path=%s', get_remote_address(request), request.url.path)
    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, _log_and_handle_rate_limit)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health.router)
app.include_router(auth.router, prefix='/api')
app.include_router(equity.router, prefix='/api')
app.include_router(ev.router, prefix='/api')
app.include_router(kelly.router, prefix='/api')
app.include_router(hand_evaluator.router, prefix='/api')
app.include_router(bots.router, prefix='/api')
app.include_router(game.router, prefix='/api')
