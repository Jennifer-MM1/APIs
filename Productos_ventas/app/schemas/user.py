from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


# --- Request Schemas ---


class UserCreate(BaseModel):
    """Schema para registro de usuario."""

    full_name: str
    email: str
    password: str


class UserLogin(BaseModel):
    """Schema para login de usuario."""

    email: str
    password: str


class UserUpdate(BaseModel):
    """Schema para actualización de usuario."""

    full_name: str | None = None
    email: str | None = None
    is_active: bool | None = None


# --- Response Schemas ---


class UserResponse(BaseModel):
    """Schema de respuesta de usuario."""

    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBriefResponse(BaseModel):
    """Schema resumido de usuario (para anidamiento en pedidos)."""

    id: int
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema de respuesta de token JWT."""

    access_token: str
    token_type: str = "bearer"
