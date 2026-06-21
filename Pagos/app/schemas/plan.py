from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.utils.enums import PlanInterval, CurrencyEnum


# --- Request Schemas ---


class PlanCreate(BaseModel):
    """Schema para crear un plan de suscripción."""

    name: str
    description: str | None = None
    amount: Decimal
    currency: CurrencyEnum = CurrencyEnum.MXN
    interval: PlanInterval = PlanInterval.MONTH
    interval_count: int = 1


class PlanUpdate(BaseModel):
    """Schema para actualizar un plan."""

    name: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    currency: CurrencyEnum | None = None
    interval: PlanInterval | None = None
    interval_count: int | None = None
    is_active: bool | None = None


# --- Response Schemas ---


class PlanResponse(BaseModel):
    """Schema de respuesta de plan."""

    id: int
    name: str
    description: str | None
    amount: Decimal
    currency: str
    interval: str
    interval_count: int
    stripe_price_id: str | None
    paypal_plan_id: str | None
    mercadopago_plan_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PlanBriefResponse(BaseModel):
    """Schema resumido de plan (para anidamiento en suscripciones)."""

    id: int
    name: str
    amount: Decimal
    currency: str
    interval: str

    model_config = ConfigDict(from_attributes=True)
