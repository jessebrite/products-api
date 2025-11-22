"""Tests for authentication endpoints."""

import pytest


def test_register_successful(client):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "john_doe"
    assert data["email"] == "john@example.com"
    assert data["is_active"] is True


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]


def test_login_successful(client):
    """Test successful login."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "nonexistent", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
