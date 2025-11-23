"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserResponse
from security import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get the current authenticated user's information."""
    user = db.query(User).filter(User.username == user.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
