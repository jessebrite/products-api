"""Unit tests for security module."""

import pytest
from src.security.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from fastapi import HTTPException, status


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_get_password_hash_returns_string(self):
        """Test that get_password_hash returns a string."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_different_each_time(self):
        """Test that get_password_hash produces different hashes each time."""
        password = "secure_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Bcrypt produces different hashes due to salt
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "secure_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test that verify_password handles empty strings."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password("", hashed) is False


class TestTokenGeneration:
    """Test JWT token creation and validation."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_three_parts(self):
        """Test that JWT token has three parts separated by dots."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiration."""
        from datetime import timedelta

        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)
        assert isinstance(token, str)
        assert len(token) > 0
