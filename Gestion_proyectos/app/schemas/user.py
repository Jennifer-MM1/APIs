from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema para crear un usuario."""

    username: str
    email: str
    password: str
    full_name: str


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario."""

    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema de respuesta de usuario (sin password)."""

    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
