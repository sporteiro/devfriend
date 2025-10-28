from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """
    Entidad de dominio User (núcleo hexagonal).
    Representa un usuario del sistema con sus datos básicos.
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
    """DTO para creación de usuario."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """DTO para login de usuario."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """DTO para respuesta de usuario (sin password)."""

    id: int
    email: EmailStr
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

