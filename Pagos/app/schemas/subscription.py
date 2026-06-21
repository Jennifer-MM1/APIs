from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.utils.enums import GatewayEnum
from app.schemas.customer import CustomerBriefResponse
from app.schemas.plan import PlanBriefResponse


# --- Request Schemas ---


class SubscriptionCreate(BaseModel):
    """Schema para crear una suscripción."""

    customer_id: int
    plan_id: int
    gateway: GatewayEnum
    payment_method_id: str | None = None  # Requerido solo para Stripe


# --- Response Schemas ---


class SubscriptionResponse(BaseModel):
    """Schema de respuesta de suscripción."""

    id: int
    customer_id: int
    plan_id: int
    gateway: str
    gateway_subscription_id: str | None
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    approval_url: str | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    customer: CustomerBriefResponse
    plan: PlanBriefResponse

    model_config = ConfigDict(from_attributes=True)


class SubscriptionBriefResponse(BaseModel):
    """Schema resumido de suscripción."""

    id: int
    gateway: str
    status: str
    plan_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
