"""Pytest configuration and fixtures."""

import os
import sqlite3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

tests_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, tests_path)

from main import app
from models import Base

import database

# Import shared fixtures
from fixtures.fixtures import auth_token, test_user_credentials, admin_user_credentials

# Use a test database file instead of in-memory (to avoid threading issues)
TEST_DB_PATH = Path(__file__).parent.parent / "test_app.db"

# Clean up any existing test database
if TEST_DB_PATH.exists():
    try:
        TEST_DB_PATH.unlink()
    except PermissionError:
        # Try again after a short delay
        time.sleep(0.5)
        try:
            TEST_DB_PATH.unlink()
        except:
            pass

# # Patch environment and settings BEFORE any imports
# os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# Recreate engine with test database
test_engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False}
)

# Replace the engine in database
database.engine = test_engine

# Create all tables
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="function")
def get_db_fixture():
    """Fixture to get database session for testing."""
    
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
    """Reset database before each test."""
    # Clear all tables
    Base.metadata.drop_all(bind=test_engine)
    # Recreate all tables  
    Base.metadata.create_all(bind=test_engine)
    yield
    # Optionally cleanup after


@pytest.fixture(scope="function")
def client(reset_db):
    """Return TestClient instance. Depends on reset_db to ensure fresh tables."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_db():
    """Clean up test database file after all tests."""
    yield
    # Close any remaining connections
    test_engine.dispose()
    # Try to delete the test database
    time.sleep(0.5)  # Brief delay to ensure connections are closed
    for attempt in range(3):
        try:
            if TEST_DB_PATH.exists():
                TEST_DB_PATH.unlink()
            break
        except PermissionError:
            if attempt < 2:
                time.sleep(0.5)
            else:
                # If it still fails, just leave it
                pass


# Export for direct imports
__all__ = ["test_engine", "test_get_db_generator", "get_db_fixture", "Base", "app", "client", "reset_db", "cleanup_test_db"]
