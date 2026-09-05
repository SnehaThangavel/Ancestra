"""Pytest fixtures for Ancestra backend tests using PostgreSQL test database."""

import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Ensure tests use the PostgreSQL test database
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", settings.TEST_DATABASE_URL)

test_engine = create_engine(
    TEST_DB_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the test database before running tests."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Optionally teardown or keep tables for future runs


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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency pointing to PostgreSQL test DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
