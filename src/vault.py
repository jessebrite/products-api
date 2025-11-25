"""Secrets vault management system."""

import os
import warnings
from typing import Any, Optional

from dotenv import load_dotenv

# Load .env file early to populate os.environ
load_dotenv()


class SecretVault:
    """Centralized secrets management system.

    This module provides a single point of access for all secrets in the application.
    Secrets are loaded from environment variables and can be accessed via this class.

    Usage:
        from vault import vault
        secret_key = vault.get_secret("SECRET_KEY")
    """

    def __init__(self) -> None:
        """Initialize the vault."""
        self._secrets_cache: dict[str, Any] = {}
        self._required_secrets = [
            "SECRET_KEY",
            "ALGORITHM",
            "DATABASE_URL",
        ]
        self._optional_secrets = [
            "SMTP_SERVER",
            "SMTP_PORT",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "SENDGRID_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "STRIPE_API_KEY",
        ]
        self._accessed_secrets: dict[str, bool] = {}

    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """Get a secret from the vault.

        Args:
            key: Secret key name (e.g., 'SECRET_KEY')
            default: Default value if secret not found

        Returns:
            Secret value

        Raises:
            ValueError: If required secret is missing
        """
        # Check cache first
        if key in self._secrets_cache:
            self._accessed_secrets[key] = True
            return self._secrets_cache[key]

        # Get from environment
        value = os.getenv(key, default)

        # Validate required secrets
        if key in self._required_secrets and value is None:
            raise ValueError(
                f"Required secret '{key}' not found in environment variables. "
                f"Please set it in your .env file or system environment."
            )

        # Cache the value
        if value is not None:
            self._secrets_cache[key] = value
            self._accessed_secrets[key] = True

            # Warn if production secret is using default/weak value
            if key == "SECRET_KEY" and ("dev" in value.lower() or len(value) < 32):
                warnings.warn(
                    f"⚠️  WARNING: '{key}' is using a weak default value! "
                    f"This is only suitable for development. "
                    f"Please set a strong secret in production.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        return value

    def has_secret(self, key: str) -> bool:
        """Check if a secret exists.

        Args:
            key: Secret key name

        Returns:
            True if secret exists, False otherwise
        """
        return os.getenv(key) is not None

    def get_all_secrets(self, include_values: bool = False) -> dict[str, Any]:
        """Get all secrets that have been accessed.

        Args:
            include_values: If True, return actual values (DANGEROUS!)
            If False, return only which secrets were accessed

        Returns:
            Dictionary of accessed secrets
        """
        if include_values:
            warnings.warn(
                "⚠️  WARNING: Returning secret values! Be careful not to log these!",
                RuntimeWarning,
                stacklevel=2,
            )
            return self._secrets_cache.copy()

        return {k: "***" for k in self._accessed_secrets if self._accessed_secrets[k]}

    def validate_secrets(self) -> dict[str, str]:
        """Validate that all required secrets are present.

        Returns:
            Dictionary with validation results

        Raises:
            ValueError: If any required secret is missing
        """
        missing = []

        for secret in self._required_secrets:
            try:
                self.get_secret(secret)
            except ValueError:
                missing.append(secret)

        if missing:
            raise ValueError(
                f"Missing required secrets: {', '.join(missing)}. "
                f"Please set them in your .env file or system environment."
            )

        return {"status": "valid", "required_secrets": self._required_secrets}

    def get_optional_secret(
        self, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get an optional secret (won't raise error if missing).

        Args:
            key: Secret key name
            default: Default value if not found

        Returns:
            Secret value or default (may be None)
        """
        return os.getenv(key, default)

    @staticmethod
    def obfuscate_secret(secret: str, show_chars: int = 4) -> str:
        """Obfuscate a secret for safe logging/display.

        Args:
            secret: Secret to obfuscate
            show_chars: Number of characters to show at start and end

        Returns:
            Obfuscated secret (e.g., "secr****key")
        """
        if len(secret) <= show_chars * 2:
            return "*" * len(secret)

        start = secret[:show_chars]
        end = secret[-show_chars:]
        middle = "*" * (len(secret) - show_chars * 2)

        return f"{start}{middle}{end}"


# Global vault instance
vault = SecretVault()


def get_vault() -> SecretVault:
    """Get the global vault instance.

    Returns:
        SecretVault instance
    """
    return vault


__all__ = ["vault", "SecretVault", "get_vault"]
