from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """
    User domain entity (hexagonal core).
    Represents a system user with their basic data.
    """

    id: Optional[int] = None
    email: EmailStr
    password_hash: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """DTO for user creation."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """DTO for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """DTO for user response (without password)."""

    id: int
    email: EmailStr
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

