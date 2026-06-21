from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.utils.enums import RefundReason


# --- Request Schemas ---


class RefundCreate(BaseModel):
    """Schema para solicitar un reembolso (total o parcial)."""

    payment_id: int
    amount: Decimal | None = None  # None = reembolso total
    reason: RefundReason = RefundReason.REQUESTED_BY_CUSTOMER
    notes: str | None = None


# --- Response Schemas ---


class RefundResponse(BaseModel):
    """Schema de respuesta de reembolso."""

    id: int
    payment_id: int
    gateway_refund_id: str | None
    amount: Decimal
    reason: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
