"""Shared pytest fixtures for backend tests.

Key insight: tests get an isolated, file-based SQLite database per test
(fast, zero external services -- no Postgres needs to be running for the
suite to pass) and a FastAPI TestClient whose `get_db` dependency is
overridden to use that SQLite session instead of whatever DATABASE_URL is
configured for real dev/prod. This is the standard FastAPI
dependency-override pattern for testing against a real (if temporary)
database rather than mocking the ORM layer.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

import backend.models  # noqa: F401 -- registers all models on Base
from backend.database import Base, get_db
from backend.main import app


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "test.db"}')
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
