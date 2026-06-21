from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


# --- Request Schemas ---


class CustomerCreate(BaseModel):
    """Schema para registrar un cliente."""

    email: str
    full_name: str
    phone: str | None = None


class CustomerUpdate(BaseModel):
    """Schema para actualizar datos de un cliente."""

    email: str | None = None
    full_name: str | None = None
    phone: str | None = None


# --- Response Schemas ---


class CustomerResponse(BaseModel):
    """Schema de respuesta de cliente."""

    id: int
    email: str
    full_name: str
    phone: str | None
    stripe_customer_id: str | None
    paypal_customer_id: str | None
    mercadopago_customer_id: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CustomerBriefResponse(BaseModel):
    """Schema resumido de cliente (para anidamiento)."""

    id: int
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)
