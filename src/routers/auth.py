"""Authentication routes."""

from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from core import (
    create_access_token,
    hash_password,
    verify_password,
)
from database import get_db
from exceptions.exceptions import (
    EmailAlreadyExistsException,
    UnauthorizedException,
    UsernameAlreadyExistsException,
)
from models import User
from schemas import Token, UserCreate, UserResponse
from tasks import log_user_action, send_welcome_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> User:
    """
    Register a new user.

    - **username**: Unique username
    - **email**: Valid email address
    - **password**: User's password

    Background tasks:
    - Send welcome email
    - Log user registration
    """

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(db_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User).where(User.username == user.username)):
            raise UsernameAlreadyExistsException(detail="Username already exists")
        raise EmailAlreadyExistsException(detail="Email already exists")

    db.refresh(db_user)

    # Add background tasks (run after response is sent)
    background_tasks.add_task(send_welcome_email, user.email, user.username)
    background_tasks.add_task(
        log_user_action, user.username, "REGISTER", f"email: {user.email}"
    )

    return db_user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict[str, str]:
    """
    Login endpoint to get JWT access token.

    - **username**: User's username
    - **password**: User's password

    Background tasks:
    - Log user login
    """
    stmt = select(User).where(User.username == form_data.username)
    user = db.scalars(stmt).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException(
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Log user login as background task
    background_tasks.add_task(
        log_user_action, user.username, "LOGIN", "successful authentication"
    )

    return {"access_token": access_token, "token_type": "bearer"}
