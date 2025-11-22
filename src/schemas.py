"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ItemBase(BaseModel):
    """Base item schema."""

    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""

    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for item response."""

    id: int
    owner_id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data."""

    username: Optional[str] = None
