from datetime import datetime
from pydantic import BaseModel, ConfigDict


# --- Request Schemas ---


class CategoryCreate(BaseModel):
    """Schema para crear categoría."""

    name: str
    description: str | None = None
    image_url: str | None = None
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    """Schema para actualizar categoría."""

    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    parent_id: int | None = None
    is_active: bool | None = None


# --- Response Schemas ---


class CategoryBriefResponse(BaseModel):
    """Schema resumido de categoría (para anidamiento)."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(BaseModel):
    """Schema de respuesta de categoría."""

    id: int
    name: str
    description: str | None
    image_url: str | None
    parent_id: int | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryWithChildrenResponse(BaseModel):
    """Schema de categoría con subcategorías."""

    id: int
    name: str
    description: str | None
    image_url: str | None
    parent_id: int | None
    is_active: bool
    created_at: datetime
    subcategories: list["CategoryBriefResponse"] = []

    model_config = ConfigDict(from_attributes=True)
