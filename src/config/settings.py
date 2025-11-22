"""Application configuration settings.

This module uses a centralized vault system to manage all secrets and configuration.
Secrets are loaded from environment variables (typically from a .env file).

See src/vault.py for the secret management system.
See .env.example for the required environment variables.
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

from vault import vault


class Settings(BaseSettings):
    """Application settings with vault-managed secrets.
    
    All sensitive values (like SECRET_KEY) are loaded from the vault
    which reads from environment variables.
    """

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # API Info (non-sensitive)
    app_name: str = "CRUD API"
    app_version: str = "1.0.0"
    app_description: str = "A secure CRUD API with JWT authentication"

    # Security (loaded from vault/environment)
    secret_key: str = ""  # Loaded via vault
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database (loaded from vault/environment)
    database_url: str = ""  # Loaded via vault

    # API
    debug: bool = False
    api_prefix: str = "/api/v1"

    def __init__(self, **data):
        """Initialize settings with vault secrets."""
        super().__init__(**data)
        
        # Load secrets from vault
        self.secret_key = vault.get_secret(
            "SECRET_KEY",
            default=self.secret_key or "your-secret-key-change-this-in-production"
        )
        self.database_url = vault.get_secret(
            "DATABASE_URL",
            default=self.database_url or "sqlite:///./app.db"
        )
        
        # Optionally override from environment if set
        if self.algorithm:
            self.algorithm = vault.get_optional_secret("ALGORITHM") or self.algorithm
        
        if self.access_token_expire_minutes:
            minutes_str = vault.get_optional_secret("ACCESS_TOKEN_EXPIRE_MINUTES")
            if minutes_str:
                self.access_token_expire_minutes = int(minutes_str)


# Global settings instance
settings = Settings()

# Validate all required secrets are available
try:
    vault.validate_secrets()
except ValueError as e:
    import warnings
    warnings.warn(f"⚠️  Secret validation warning: {e}", RuntimeWarning)
