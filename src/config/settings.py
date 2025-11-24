"""Application configuration settings.

This module uses a centralized vault system to manage all secrets and configuration.
Secrets are loaded from environment variables (typically from a .env file).

See src/vault.py for the secret management system.
See .env.example for the required environment variables.
"""

import logging
import os
import tomllib
from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

from vault import vault

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def read_pyproject_metadata() -> tuple[str, str, str]:
    """Read project metadata from pyproject.toml and version.txt.

    Returns:
        Tuple[str, str, str]: (app_name, app_description, app_version)
    """
    default_name = "CRUD API"
    default_description = "A secure CRUD API with JWT authentication"
    default_version = "0.1.1"

    app_name = default_name
    app_description = default_description
    app_version = default_version

    base_path = Path(__file__).parent.parent.parent.resolve()
    pyproject_path = os.path.join(base_path, "pyproject.toml")
    version_path = os.path.join(base_path, "version.txt")

    try:
        # Load pyproject.toml
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
            project_data = pyproject_data.get("project", {})
            app_name = project_data.get("name") or default_name
            app_description = project_data.get("description") or default_description

        # Load version.txt if exists
        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as vf:
                version_content = vf.read().strip()
                app_version = version_content if version_content else default_version

        logger.info(
            f"Loaded app_name='{app_name}', app_description='{app_description}'"
            f" , app_version='{app_version}'"
        )

    except Exception as error:
        logger.error(f"Error reading project metadata: {error} ")
        logger.error("Using default metadata values.")

    return app_name, app_description, app_version


class Settings(BaseSettings):
    """Application settings with vault-managed secrets.

    All sensitive values (like SECRET_KEY) are loaded from the vault
    which reads from environment variables.
    """

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # API Info (non-sensitive) - loaded dynamically from pyproject.toml and version.txt
    app_name: str
    app_version: str
    app_description: str

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
        # Read project metadata
        app_name, app_description, app_version = read_pyproject_metadata()
        # Set metadata if not explicitly provided
        data.setdefault("app_name", app_name)
        data.setdefault("app_description", app_description)
        data.setdefault("app_version", app_version)

        super().__init__(**data)

        # Load secrets from vault
        self.secret_key = vault.get_secret("SECRET_KEY", default=self.secret_key)
        self.database_url = vault.get_secret("DATABASE_URL", default=self.database_url)

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
