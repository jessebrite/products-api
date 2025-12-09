"""Application configuration settings.

This module uses a centralized vault system to manage all secrets and configuration.
Secrets are loaded from environment variables (typically from a .env file).

See src/vault.py for the secret management system.
"""

import os
from pathlib import Path
from typing import Any

import tomli
from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

from logger import logger
from vault import vault


def read_pyproject_metadata() -> tuple[str, str, str]:
    """Read project metadata from pyproject.toml and version.txt.

    Returns:
        Tuple[str, str, str]: (app_name, app_description, app_version)
    """
    default_name = "CRUD API"
    default_description = "A secure CRUD API with JWT authentication"
    default_version = "0.1.0"

    app_name = default_name
    app_description = default_description
    app_version = default_version

    base_path = Path(__file__).resolve().parent.parent.parent
    pyproject_path = base_path / "pyproject.toml"
    version_path = base_path / "version.txt"

    try:
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
            project_data = pyproject_data.get("project", {})
            app_name = project_data.get("name") or default_name
            app_description = project_data.get("description") or default_description

        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as vf:
                version_content = vf.read().strip()
                app_version = version_content if version_content else default_version

        logger.info(
            f"Loaded app_name='{app_name}', app_description='{app_description}'"
            f" , app_version='{app_version}'"
        )

    except FileNotFoundError as error:
        logger.error(f"File doesn't exist: {error} ")
        logger.error("Using default metadata values.")

    except Exception as error:
        logger.error(f"Error reading project metadata: {error} ")
        logger.error("Using default metadata values.")

    return app_name, app_description, app_version


class Settings(BaseSettings):
    """Application settings with vault-managed secrets.

    All sensitive values (like SECRET_KEY) are loaded from the vault
    which reads from environment variables.
    """

    debug: bool = False

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    app_name: str = Field(
        default="CRUD API", description="Application name from pyproject.toml"
    )
    app_version: str = Field(
        default="0.1.0", description="Application version from version.txt"
    )
    app_description: str = Field(
        default="A secure CRUD API with JWT authentication",
        description="Application description from pyproject.toml",
    )

    secret_key: str = Field(min_length=32)
    algorithm: str = Field(default="HS256", pattern=r"^[A-Za-z0-9]+$")
    database_url: str = Field(default="")
    access_token_expire_minutes: int = 30

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_expiry(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Token expiry must be positive")
        return v

    # API
    debug: bool = False
    api_prefix: str = "/api/v1"

    def __init__(self, **data: Any) -> None:
        app_name, app_description, app_version = read_pyproject_metadata()
        data.setdefault("app_name", app_name)
        data.setdefault("app_description", app_description)
        data.setdefault("app_version", app_version)

        super().__init__(**data)

    @model_validator(mode="after")
    def load_secrets(self) -> "Settings":
        self.secret_key = vault.get_secret("SECRET_KEY", default=self.secret_key)
        self.database_url = vault.get_secret("DATABASE_URL", default=self.database_url)
        self.algorithm = vault.get_optional_secret("ALGORITHM") or self.algorithm

        if minutes_str := vault.get_optional_secret("ACCESS_TOKEN_EXPIRE_MINUTES"):
            self.access_token_expire_minutes = int(minutes_str)

        return self


settings = Settings()

try:
    vault.validate_secrets()
except ValueError as e:
    logger.warning(f"⚠️  Secret validation warning: {e}", RuntimeWarning)
