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
from backend.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """The Limiter instance is a module-level singleton shared by every
    test (TestClient requests all appear to come from the same fake IP),
    so without resetting it, hitting a strict bucket (e.g. AUTH_LIMIT,
    5/15min) in one test starves every later test that calls the same
    endpoint. Reset before AND after so a test that deliberately exhausts
    the limit doesn't poison whatever runs next either."""
    limiter.reset()
    yield
    limiter.reset()


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


def signup_and_get_headers(client, email):
    """Signs up a fresh user and returns an Authorization header dict
    ready to pass to any protected endpoint -- shared by any test file
    that needs an authenticated client (game router, future auth-gated
    routers) rather than repeating the signup dance in each one."""
    response = client.post('/api/auth/signup', json={'email': email, 'password': 'correct-horse-battery'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def auth_headers(client):
    return signup_and_get_headers(client, 'hero@example.com')
