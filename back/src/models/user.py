from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    """
    User domain entity (hexagonal core).
    Represents a system user with their basic data.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    email: EmailStr
    password_hash: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


class UserCreate(BaseModel):
    """DTO for user creation."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """DTO for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime
    is_active: bool
