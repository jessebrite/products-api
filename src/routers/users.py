"""User routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserResponse
from security import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user's information."""

    stmt = select(User).where(User.username == user.username)
    return db.scalars(stmt).first()
