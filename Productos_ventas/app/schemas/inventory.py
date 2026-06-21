from datetime import datetime
from pydantic import BaseModel, ConfigDict


# --- Request Schemas ---


class InventoryUpdate(BaseModel):
    """Schema para actualizar inventario."""

    stock: int | None = None
    min_stock: int | None = None


class RestockRequest(BaseModel):
    """Schema para registrar un restock."""

    quantity: int  # Cantidad a agregar al stock actual


# --- Response Schemas ---


class InventoryResponse(BaseModel):
    """Schema de respuesta de inventario."""

    id: int
    product_id: int
    stock: int
    min_stock: int
    last_restock: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class InventoryWithProductResponse(BaseModel):
    """Schema de inventario con datos del producto."""

    id: int
    product_id: int
    stock: int
    min_stock: int
    last_restock: datetime | None
    updated_at: datetime | None
    product_name: str
    product_sku: str
    is_low_stock: bool

    model_config = ConfigDict(from_attributes=True)
