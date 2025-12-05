"""Pydantic schemas for API validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
    )


class UserBase(StrictModel):
    """Base user schema."""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class ItemBase(StrictModel):
    """Base item schema."""

    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(StrictModel):
    """Schema for updating an item."""

    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime


class Token(StrictModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str


class TokenData(StrictModel):
    """Schema for token data."""

    username: Optional[str] = None
