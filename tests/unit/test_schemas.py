"""Unit tests for schemas and models."""

import pytest
from pydantic import ValidationError

from schemas import UserCreate, UserResponse, ItemCreate, ItemResponse

class TestUserCreateSchema:
    """Test UserCreate schema validation."""

    def test_valid_user_create(self):
        """Test creating a valid UserCreate object."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
        user = UserCreate(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"

    def test_user_create_missing_username(self):
        """Test that UserCreate requires username."""
        user_data = {"email": "test@example.com", "password": "password123"}
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_missing_email(self):
        """Test that UserCreate requires email."""
        user_data = {"username": "testuser", "password": "password123"}
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_missing_password(self):
        """Test that UserCreate requires password."""
        user_data = {"username": "testuser", "email": "test@example.com"}
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_invalid_email(self):
        """Test that UserCreate validates email format."""
        user_data = {
            "username": "testuser",
            "email": "not-an-email",
            "password": "password123",
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)


class TestItemCreateSchema:
    """Test ItemCreate schema validation."""

    def test_valid_item_create(self):
        """Test creating a valid ItemCreate object."""
        item_data = {
            "title": "Test Item",
            "description": "A test item",
        }
        item = ItemCreate(**item_data)
        assert item.title == "Test Item"
        assert item.description == "A test item"

    def test_item_create_missing_title(self):
        """Test that ItemCreate requires title."""
        item_data = {"description": "A test item"}
        with pytest.raises(ValidationError):
            ItemCreate(**item_data)

    def test_item_create_with_optional_description(self):
        """Test that ItemCreate description is optional."""
        item_data = {"title": "Test Item"}
        item = ItemCreate(**item_data)
        assert item.title == "Test Item"
        assert item.description is None or item.description == ""
