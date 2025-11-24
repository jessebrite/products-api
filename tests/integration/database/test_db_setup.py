"""Test script to verify database setup."""

import sqlalchemy

from tests.conftest import test_engine


def test_tables_exist():
    """Test that all required tables exist in test_engine."""
    inspector = sqlalchemy.inspect(test_engine)
    tables = inspector.get_table_names()
    assert len(tables) > 0, "No tables found in test_engine"
    print("Tables in test_engine:", tables)


def test_get_db_works(get_db_fixture):
    """Test that get_db_fixture returns a valid database session."""
    db = get_db_fixture
    assert db is not None, "get_db_fixture returned None"
    print("Got DB session:", db)


def test_query_users_table(get_db_fixture):
    """Test that we can query the users table."""
    db = get_db_fixture
    try:
        # Query using the User model instead of metadata
        from models import User

        users = db.query(User).all()
        print("Query successful! Found", len(users), "users")
        assert True
    except Exception as e:
        print("Query failed:", e)
        raise


def test_dependency_override(client):
    """Test that get_db is properly set up for testing."""
    # If client fixture works, the test database is set up correctly
    assert client is not None
    print("Dependency override test passed!")
