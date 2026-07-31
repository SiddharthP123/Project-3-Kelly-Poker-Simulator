"""Stand up the schema against whatever DATABASE_URL points at.

No Alembic yet (see README Part 8 notes) -- this is deliberately just
`create_all()` until the schema needs to change without dropping data.

Run from the project root:
    source venv/bin/activate
    PYTHONPATH=. python3 backend/create_tables.py
"""

from backend.database import Base, engine
from backend.models import (  # noqa: F401 -- import registers models
    BankrollLog,
    GameSession,
    GameSessionOpponent,
    HandAction,
    HandHistory,
    HandPlayer,
    User,
)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    print(f'Tables created against {engine.url}')
