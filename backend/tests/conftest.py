"""
Shared pytest fixtures.

Environment is configured for tests BEFORE any app module is imported: an
isolated temp SQLite DB and the deterministic fake LLM provider, so tests never
touch a network or a real API key (spec §21).
"""

import os
import tempfile

os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long-000000")
_DB_FD, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models as _models  # noqa: E402,F401  (registers tables; aliased so it
from app.db.base import Base, engine  # noqa: E402  # doesn't shadow the `app` instance
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_db():
    """Fresh schema for every test → full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    gen = get_db()
    session = next(gen)
    try:
        yield session
    finally:
        gen.close()


@pytest.fixture
def auth_headers(client):
    """Register a user and return Authorization headers."""
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password123", "full_name": "Test User"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def second_user_headers(client):
    r = client.post(
        "/api/v1/auth/register", json={"email": "other@example.com", "password": "password123"}
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def create_completed_project(client, headers, **overrides):
    """Helper: create a project (runs synchronously in TestClient) and return its detail."""
    payload = {
        "title": "Test project",
        "product_description": "A test product that does something useful for people.",
        "target_audience": "People who need the test product.",
        "research_goal": "Decide what to build first.",
        "num_personas": 3,
        "num_questions": 4,
    }
    payload.update(overrides)
    r = client.post("/api/v1/research", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json()
