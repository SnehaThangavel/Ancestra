"""Pytest fixtures for Ancestra backend tests using PostgreSQL test database."""

import os
import uuid
from datetime import datetime, timezone
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, get_db
from app.models.user import User
from app.auth.jwt_handler import create_access_token
from app.main import app

import json
import sqlite3

sqlite3.register_adapter(dict, json.dumps)
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, ARRAY
from sqlalchemy.types import JSON

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"

# Ensure tests use the PostgreSQL test database or fallback to SQLite in-memory for testing
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", settings.TEST_DATABASE_URL)
if TEST_DB_URL.startswith("postgresql://"):
    TEST_DB_URL = TEST_DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

try:
    test_engine = create_engine(
        TEST_DB_URL,
        pool_pre_ping=True,
        json_serializer=lambda obj: json.dumps(obj, default=str),
    )
    with test_engine.connect() as _test_conn:
        pass
except Exception:
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        json_serializer=lambda obj: json.dumps(obj, default=str),
    )

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the test database before running tests."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    # Keep tables for inspection



@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a clean PostgreSQL database session per test with automatic cleanup."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def in_memory_db(db_session: Session) -> Session:
    """Alias for backwards compatibility with tests originally written for in-memory SQLite."""
    return db_session


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Fixture providing an active registered test User."""
    user = User(
        id=uuid.uuid4(),
        email="test_curator@heritage.org",
        name="Test Curator",
        google_sub_id=f"google_sub_{uuid.uuid4().hex[:10]}",
        picture_url="https://example.com/curator.jpg",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        last_login_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Fixture providing a valid JWT Bearer access token for the test user."""
    return create_access_token(user_id=test_user.id, email=test_user.email)


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Fixture providing standard Authorization Bearer header dict."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client(db_session: Session, test_user: User, auth_token: str) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden DB and pre-injected Authorization header."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"Authorization": f"Bearer {auth_token}"}) as c:
        yield c
    app.dependency_overrides.clear()
