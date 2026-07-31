"""Importing this package registers all models on the shared declarative
Base -- required before SQLAlchemy can resolve the string-based
relationship() references between them (e.g. GameSession -> HandHistory)."""

from backend.models.bankroll_log import BankrollLog
from backend.models.game_session import GameSession
from backend.models.game_session_opponent import GameSessionOpponent
from backend.models.hand_action import HandAction
from backend.models.hand_history import HandHistory
from backend.models.hand_player import HandPlayer
from backend.models.user import User

__all__ = [
    'User', 'GameSession', 'GameSessionOpponent', 'HandHistory', 'HandPlayer', 'HandAction',
    'BankrollLog',
]
