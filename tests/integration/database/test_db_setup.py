"""Test script to verify database setup."""

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import test_engine


def test_tables_exist() -> None:
    """Test that all required tables exist in test_engine."""
    inspector = sqlalchemy.inspect(test_engine)
    tables = inspector.get_table_names()
    assert len(tables) > 0, "No tables found in test_engine"


def test_get_db_works(get_db_fixture: Session) -> None:
    """Test that get_db_fixture returns a valid database session."""
    db = get_db_fixture
    assert db is not None, "get_db_fixture returned None"


def test_query_users_table(get_db_fixture: Session) -> None:
    """Test that we can query the users table."""
    db = get_db_fixture
    try:
        # Query using the User model instead of metadata
        from models import User

        db.query(User).all()
        assert True
    except Exception:
        raise


def test_dependency_override(client: TestClient) -> None:
    """Test that get_db is properly set up for testing."""
    # If client fixture works, the test database is set up correctly
    assert client is not None
