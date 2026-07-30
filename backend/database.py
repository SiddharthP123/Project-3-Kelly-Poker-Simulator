"""SQLAlchemy engine/session setup.

Key insight: FastAPI's dependency injection (`Depends(get_db)`) is what
guarantees every request gets its own database session and that session
always gets closed afterward, even if the request handler raises -- the
`try/finally` here runs regardless of how the `yield` caller exits.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
