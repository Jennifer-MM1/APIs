from enum import Enum


class GatewayEnum(str, Enum):
    """Pasarelas de pago soportadas."""

    STRIPE = "stripe"
    PAYPAL = "paypal"
    MERCADOPAGO = "mercadopago"


class PaymentStatus(str, Enum):
    """Estados posibles de un pago."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, Enum):
    """Estados posibles de una suscripción."""

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    EXPIRED = "expired"


class RefundStatus(str, Enum):
    """Estados posibles de un reembolso."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class RefundReason(str, Enum):
    """Razones para solicitar un reembolso."""

    REQUESTED_BY_CUSTOMER = "requested_by_customer"
    DUPLICATE = "duplicate"
    FRAUDULENT = "fraudulent"
    OTHER = "other"


class PlanInterval(str, Enum):
    """Intervalos de facturación para planes de suscripción."""

    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class CurrencyEnum(str, Enum):
    """Monedas soportadas."""

    MXN = "MXN"
    USD = "USD"
