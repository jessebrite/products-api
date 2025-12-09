"""Security utilities for JWT authentication and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import bcrypt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from exceptions.exceptions import (
    InactiveUserException,
    NotFoundException,
    ValidationException,
)
from models import User

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token", auto_error=False
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(
    data: dict[str, str], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Validate JWT token and return the user."""
    if not token:
        raise NotFoundException(detail="Missing token")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
        username: str = payload.get("sub")
        if username is None:
            raise NotFoundException(detail="Invalid token: missing 'sub' claim")
    except JWTError:
        raise ValidationException(detail="Invalid or expired token")

    stmt = select(User).where(User.username == username)
    user = db.scalars(stmt).first()
    if not user:
        raise NotFoundException(detail="User not found")

    if not user.is_active:
        raise InactiveUserException(detail="Inactive user")
    return user
