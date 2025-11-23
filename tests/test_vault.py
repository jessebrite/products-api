import pytest
import os
import warnings
from unittest.mock import patch

from src.vault import SecretVault, vault, get_vault


@pytest.fixture(autouse=True)
def clear_cache():
    vault._secrets_cache.clear()
    vault._accessed_secrets.clear()
    yield
    vault._secrets_cache.clear()
    vault._accessed_secrets.clear()


@pytest.mark.parametrize("env_dict, key, expected_value", [
    ({"SECRET_KEY": "mysecretkey123456789012345678901234"}, "SECRET_KEY", "mysecretkey123456789012345678901234"),
    ({}, "SMTP_SERVER", "smtp.test"),
])
def test_get_secret(env_dict, key, expected_value):
    with patch.dict(os.environ, env_dict, clear=True):
        if key == "SECRET_KEY":
            value = vault.get_secret(key)
            assert value == expected_value
        else:
            value = vault.get_secret(key, default="smtp.test")
            assert value == expected_value


def test_get_secret_missing_required_raises():
    vault._secrets_cache.clear()
    with patch.dict(os.environ, {}, clear=True):
        if "SECRET_KEY" in vault._secrets_cache:
            del vault._secrets_cache["SECRET_KEY"]
        with pytest.raises(ValueError):
            vault.get_secret("SECRET_KEY")


def test_get_secret_warns_for_weak_secret_key():
    with patch.dict(os.environ, {"SECRET_KEY": "weaksecret"}):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            vault.get_secret("SECRET_KEY")
            assert any("WARNING" in str(warn.message) for warn in w)


@pytest.mark.parametrize("env_dict, key, expected", [
    ({"NEW_SECRET": "value"}, "NEW_SECRET", True),
    ({}, "UNKNOWN_SECRET", False),
])
def test_has_secret(env_dict, key, expected):
    with patch.dict(os.environ, env_dict, clear=True):
        assert vault.has_secret(key) is expected


def test_get_all_secrets_mask_and_values():
    with patch.dict(os.environ, {"SECRET_KEY": "secretvalue"}):
        vault.get_secret("SECRET_KEY")
        masked = vault.get_all_secrets(include_values=False)
        assert masked.get("SECRET_KEY") == "***"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            values = vault.get_all_secrets(include_values=True)
            assert values.get("SECRET_KEY") == "secretvalue"
            assert any("WARNING" in str(warn.message) for warn in w)


@pytest.mark.parametrize("env_dict, should_raise", [
    ({"SECRET_KEY": "a"*32, "ALGORITHM": "HS256", "DATABASE_URL": "dburl"}, False),
    ({}, True),
])
def test_validate_secrets(env_dict, should_raise):
    vault._secrets_cache.clear()
    with patch.dict(os.environ, env_dict, clear=True):
        if should_raise:
            with pytest.raises(ValueError):
                vault.validate_secrets()
        else:
            result = vault.validate_secrets()
            assert result.get("status") == "valid"


@pytest.mark.parametrize("env_val, key, expected", [
    ("smtp.test", "SMTP_SERVER", "smtp.test"),
    (None, "SMTP_SERVER", "defval"),
])
def test_get_optional_secret(env_val, key, expected):
    env = {key: env_val} if env_val is not None else {}
    with patch.dict(os.environ, env, clear=True):
        assert vault.get_optional_secret(key, default="defval") == expected


@pytest.mark.parametrize("secret, show_chars, expected_start, expected_end, expected_mask", [
    ("abcdefghij", 3, "abc", "hij", True),
    ("abcd", 3, "", "", False),
])
def test_obfuscate_secret(secret, show_chars, expected_start, expected_end, expected_mask):
    obfuscated = SecretVault.obfuscate_secret(secret, show_chars=show_chars)
    if expected_mask:
        assert obfuscated.startswith(expected_start) and obfuscated.endswith(expected_end)
        assert "*" in obfuscated
    else:
        assert obfuscated == "*" * len(secret)


def test_get_vault_returns_singleton():
    v1 = get_vault()
    v2 = get_vault()
    assert v1 is v2
    assert v1 is vault
