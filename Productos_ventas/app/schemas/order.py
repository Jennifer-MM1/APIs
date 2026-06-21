from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserBriefResponse
from app.schemas.product import ProductBriefResponse


# --- Request Schemas ---


class OrderItemCreate(BaseModel):
    """Schema para un item dentro de un pedido."""

    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    """Schema para crear un pedido (operación de venta)."""

    items: list[OrderItemCreate]
    shipping_address: str | None = None
    notes: str | None = None


class OrderStatusUpdate(BaseModel):
    """Schema para actualizar el estado de un pedido."""

    status: str  # pending, confirmed, shipped, delivered, cancelled


# --- Response Schemas ---


class OrderItemResponse(BaseModel):
    """Schema de respuesta de item de pedido."""

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    product: ProductBriefResponse

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Schema de respuesta de pedido."""

    id: int
    order_number: str
    user_id: int
    status: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    shipping_address: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None
    user: UserBriefResponse
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderBriefResponse(BaseModel):
    """Schema resumido de pedido (para listados)."""

    id: int
    order_number: str
    status: str
    total: Decimal
    created_at: datetime
    items_count: int

    model_config = ConfigDict(from_attributes=True)
