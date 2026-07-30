"""FastAPI application entrypoint.

Run locally with:
    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.rate_limit import limiter
from backend.routers import bots, equity, ev, game, hand_evaluator, health, kelly

app = FastAPI(title='Kelly Poker Simulator API')
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health.router)
app.include_router(equity.router, prefix='/api')
app.include_router(ev.router, prefix='/api')
app.include_router(kelly.router, prefix='/api')
app.include_router(hand_evaluator.router, prefix='/api')
app.include_router(bots.router, prefix='/api')
app.include_router(game.router, prefix='/api')
