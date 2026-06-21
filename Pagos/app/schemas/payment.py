from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.utils.enums import GatewayEnum, CurrencyEnum, PaymentStatus
from app.schemas.customer import CustomerBriefResponse


# --- Request Schemas ---


class PaymentCreate(BaseModel):
    """Schema para crear un pago.

    - Para Stripe: se necesita un `payment_method_id` del frontend (Stripe.js).
    - Para PayPal: se crea una orden y se retorna `checkout_url` para redirect.
    - Para MercadoPago: se crea una preferencia y se retorna `checkout_url`.
    """

    customer_id: int
    gateway: GatewayEnum
    amount: Decimal
    currency: CurrencyEnum = CurrencyEnum.MXN
    description: str | None = None
    payment_method_id: str | None = None  # Requerido solo para Stripe
    metadata: dict | None = None


# --- Response Schemas ---


class PaymentResponse(BaseModel):
    """Schema de respuesta de pago."""

    id: int
    payment_number: str
    customer_id: int
    gateway: str
    gateway_payment_id: str | None
    amount: Decimal
    currency: str
    status: str
    description: str | None
    checkout_url: str | None
    created_at: datetime
    updated_at: datetime | None
    customer: CustomerBriefResponse

    model_config = ConfigDict(from_attributes=True)


class PaymentBriefResponse(BaseModel):
    """Schema resumido de pago."""

    id: int
    payment_number: str
    gateway: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    """Schema para listar pagos con paginación."""

    total: int
    payments: list[PaymentBriefResponse]
