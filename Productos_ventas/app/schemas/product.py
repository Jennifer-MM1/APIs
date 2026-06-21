from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.category import CategoryBriefResponse
from app.schemas.inventory import InventoryResponse


# --- Request Schemas ---


class ProductCreate(BaseModel):
    """Schema para crear producto."""

    name: str
    sku: str
    description: str | None = None
    price: Decimal
    brand: str | None = None
    image_url: str | None = None
    category_id: int
    initial_stock: int = 0  # Stock inicial al crear el producto
    min_stock: int = 5  # Umbral mínimo de stock


class ProductUpdate(BaseModel):
    """Schema para actualizar producto."""

    name: str | None = None
    sku: str | None = None
    description: str | None = None
    price: Decimal | None = None
    brand: str | None = None
    image_url: str | None = None
    category_id: int | None = None
    is_active: bool | None = None


# --- Response Schemas ---


class ProductResponse(BaseModel):
    """Schema de respuesta de producto."""

    id: int
    name: str
    sku: str
    description: str | None
    price: Decimal
    brand: str | None
    image_url: str | None
    category_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    category: CategoryBriefResponse
    inventory: InventoryResponse | None

    model_config = ConfigDict(from_attributes=True)


class ProductBriefResponse(BaseModel):
    """Schema resumido de producto (para anidamiento en pedidos)."""

    id: int
    name: str
    sku: str
    price: Decimal
    brand: str | None

    model_config = ConfigDict(from_attributes=True)
