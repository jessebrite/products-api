"""Unit tests for security module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from jose import JWTError

from src.models import User
from src.security.security import (
    AuthException,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_get_password_hash_returns_string(self) -> None:
        """Test that get_password_hash returns a string."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_different_each_time(self) -> None:
        """Test that get_password_hash produces different hashes each time."""
        password = "secure_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Bcrypt produces different hashes due to salt
        assert hash1 != hash2

    def test_verify_password_correct(self) -> None:
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

    def test_verify_password_empty_string(self) -> None:
        """Test that verify_password handles empty strings."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password("", hashed) is False


class TestTokenGeneration:
    """Test JWT token creation and validation."""

    def test_create_access_token_returns_string(self) -> None:
        """Test that create_access_token returns a string."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_three_parts(self) -> None:
        """Test that JWT token has three parts separated by dots."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_with_custom_expiry(self) -> None:
        """Test creating token with custom expiration."""
        from datetime import timedelta

        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)
        assert isinstance(token, str)
        assert len(token) > 0


class TestGetCurrentUser:
    """Test get_current_user function."""

    @patch("src.security.security.settings")
    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_valid_token_active_user(
        self, mock_jwt_decode: Mock, mock_settings: Mock, get_db_fixture
    ) -> None:
        """Test valid token with active user returns the user."""
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"

        mock_jwt_decode.return_value = {"sub": "testuser", "exp": 1234567890}

        mock_user = MagicMock(spec=User)
        mock_user.is_active = True
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_user

        with patch.object(get_db_fixture, "scalars", return_value=mock_scalars):
            # Call the function
            result = await get_current_user(token="valid_token", db=get_db_fixture)

        # Assertions
        assert result == mock_user
        mock_jwt_decode.assert_called_once_with(
            "valid_token",
            "test_secret",
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )

    @pytest.mark.asyncio
    async def test_missing_token_raises_exception(self, get_db_fixture) -> None:
        """Test that missing token raises AuthException."""
        with pytest.raises(AuthException) as exc_info:
            await get_current_user(token=None, db=get_db_fixture)

        assert exc_info.value.detail == "Missing token"

    @patch("src.security.security.settings")
    @patch("src.security.security.jwt.decode")
    @pytest.mark.asyncio
    async def test_valid_token_inactive_user(
        self, mock_jwt_decode: Mock, mock_settings: Mock, get_db_fixture
    ) -> None:
        """Test valid token with inactive user raises AuthException."""
        # Mock settings
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"

        # Mock JWT decode to return valid payload
        mock_jwt_decode.return_value = {"sub": "testuser", "exp": 1234567890}

        mock_user = MagicMock(spec=User)
        mock_user.is_active = True
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_user

        mock_user = Mock(spec=User)
        mock_user.is_active = False
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_user

        with patch.object(get_db_fixture, "scalars", return_value=mock_scalars):
            with pytest.raises(AuthException) as exc_info:
                await get_current_user(token="valid_token", db=get_db_fixture)

        assert str(exc_info.value.detail) == "Inactive user"
        mock_jwt_decode.assert_called_once_with(
            "valid_token",
            "test_secret",
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )

    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_invalid_jwt_token(
        self, mock_jwt_decode: Mock, get_db_fixture
    ) -> None:
        """Test invalid/malformed JWT token raises AuthException."""
        mock_jwt_decode.side_effect = JWTError("Invalid token")

        # Call the function and expect exception
        with pytest.raises(AuthException) as exc_info:
            await get_current_user(token="invalid_token", db=get_db_fixture)

        assert exc_info.value.detail == "Invalid or expired token"

    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_token_missing_sub_claim(
        self, mock_jwt_decode: Mock, get_db_fixture
    ) -> None:
        """Test token missing 'sub' claim raises AuthException."""
        mock_jwt_decode.return_value = {"some_other_key": "value", "exp": 1234567890}

        with pytest.raises(AuthException) as exc_info:
            await get_current_user(token="token_without_sub", db=get_db_fixture)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token: missing 'sub' claim"

    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_token_non_existent_user(
        self, mock_jwt_decode: Mock, get_db_fixture
    ) -> None:
        """Test token for non-existent user raises AuthException."""
        # Mock JWT decode to return valid payload
        mock_jwt_decode.return_value = {"sub": "nonexistent", "exp": 1234567890}

        # Mock database to return None
        mock_scalars = Mock()
        mock_scalars.first.return_value = None

        with patch.object(get_db_fixture, "scalars", return_value=mock_scalars):
            # Call the function and expect exception
            with pytest.raises(AuthException) as exc_info:
                await get_current_user(token="token_for_nonexistent", db=get_db_fixture)

        assert exc_info.value.detail == "User not found"

    @patch("src.security.security.settings")
    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_token_inactive_user(
        self, mock_jwt_decode: Mock, mock_settings: Mock, get_db_fixture
    ) -> None:
        """Test token for inactive user raises AuthException."""
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"
        mock_jwt_decode.return_value = {"sub": "testuser", "exp": 1234567890}

        mock_user = Mock(spec=User)
        mock_user.is_active = False
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_user

        with patch.object(get_db_fixture, "scalars", return_value=mock_scalars):
            with pytest.raises(AuthException) as exc_info:
                await get_current_user(token="token_for_inactive", db=get_db_fixture)

        assert exc_info.value.detail == "Inactive user"

    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_expired_token(self, mock_jwt_decode: Mock, get_db_fixture) -> None:
        """Test expired token raises AuthException."""
        mock_jwt_decode.side_effect = JWTError("Token has expired")

        # Call the function and expect exception
        with pytest.raises(AuthException) as exc_info:
            await get_current_user(token="expired_token", db=get_db_fixture)

        assert exc_info.value.detail == "Invalid or expired token"

    @patch("jose.jwt.decode")
    @pytest.mark.asyncio
    async def test_invalid_signature_token(
        self, mock_jwt_decode: Mock, get_db_fixture
    ) -> None:
        """Test token with invalid signature raises AuthException."""
        mock_jwt_decode.side_effect = JWTError("Invalid signature")

        # Call the function and expect exception
        with pytest.raises(AuthException) as exc_info:
            await get_current_user(token="invalid_signature_token", db=get_db_fixture)

        assert exc_info.value.detail == "Invalid or expired token"
