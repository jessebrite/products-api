"""Pytest configuration and fixtures."""

import os
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Patch environment and settings BEFORE any application imports
# This is the crucial part to prevent the app from using the production DB during tests

TEST_DB_PATH: Path = Path(__file__).parent.parent / "test_app.db"

if os.environ.get("CI"):
    os.environ["DATABASE_URL"] = f"sqlite:///{Path('/tmp') / 'test_ci.db'}"
else:
    os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"


# Add src and tests to path to allow for imports
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, src_path)

tests_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, tests_path)

# Now that the environment is patched, we can import the application
# Import shared fixtures
from fixtures.fixtures import admin_user_credentials, auth_token, test_user_credentials

import database
from main import app
from models import Base

# Create a new engine with the test database URL
if os.environ.get("CI"):
    test_engine = create_engine(
        f"sqlite:///{Path('/tmp') / 'test_ci.db'}",
        connect_args={"check_same_thread": False},
    )
else:
    test_engine = create_engine(
        f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False}
    )

# Replace the engine in the database module with the test engine
database.engine = test_engine

# Create all tables in the test database
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def set_test_db_url():
    """Ensure the DATABASE_URL is set for the entire test session."""
    if os.environ.get("CI"):
        os.environ["DATABASE_URL"] = f"sqlite:///{Path('/tmp') / 'test_ci.db'}"
    else:
        os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="function")
def get_db_fixture():
    """Fixture to get a database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset the database before each test to ensure isolation."""
    # Clear all tables
    Base.metadata.drop_all(bind=test_engine)
    # Recreate all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Optional cleanup after yield if needed


@pytest.fixture(scope="function")
def client(reset_db: None):
    """Return a TestClient instance for making API requests.

    Depends on reset_db to ensure a fresh database for each test.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_db():
    """Clean up the test database file after all tests are done."""
    yield
    # Close any remaining connections to the database
    test_engine.dispose()
    # Add a brief delay to ensure all connections are closed before deleting the file
    time.sleep(0.5)
    for attempt in range(3):
        try:
            if TEST_DB_PATH.exists():
                TEST_DB_PATH.unlink()
            break
        except PermissionError:
            if attempt < 2:
                time.sleep(0.5)
            else:
                # If it still fails after multiple attempts, just leave it.
                pass


# tests/conftest.py (or any conftest in tests/)
def pytest_collection_modifyitems(items):
    # If a test file is inside tests/integration/, auto-mark it as integration
    for item in items:
        if "tests/integration" in item.nodeid:
            item.add_marker("integration")


# Export fixtures for direct imports in other test files
__all__ = [
    "test_engine",
    "get_db_fixture",
    "Base",
    "app",
    "client",
    "reset_db",
    "cleanup_test_db",
    "auth_token",
    "test_user_credentials",
    "admin_user_credentials",
]
