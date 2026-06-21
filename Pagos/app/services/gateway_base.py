from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass
class GatewayResponse:
    """Respuesta estandarizada de cualquier operación con una pasarela.

    Todos los gateways retornan esta estructura para uniformar
    el manejo de resultados en los routers.
    """

    success: bool
    gateway_id: str | None = None  # ID del recurso en la pasarela
    status: str = "pending"
    checkout_url: str | None = None  # URL de redirect (PayPal, MercadoPago)
    raw_response: dict = field(default_factory=dict)  # Respuesta completa de la pasarela
    error_message: str | None = None


@dataclass
class WebhookEvent:
    """Evento de webhook parseado y verificado."""

    event_id: str
    event_type: str  # Ej: "payment.completed", "subscription.cancelled"
    gateway: str
    resource_id: str | None = None  # ID del pago/suscripción afectado
    data: dict = field(default_factory=dict)  # Datos del evento


class PaymentGateway(ABC):
    """Interfaz abstracta para pasarelas de pago (Strategy Pattern).

    Cada gateway (Stripe, PayPal, MercadoPago) implementa estos métodos.
    El factory (gateway_factory.py) decide cuál instanciar según el request.
    """

    # --- Clientes ---

    @abstractmethod
    def create_customer(self, email: str, full_name: str, **kwargs) -> GatewayResponse:
        """Registra un cliente en la pasarela externa."""
        ...

    # --- Pagos ---

    @abstractmethod
    def create_payment(
        self,
        amount: Decimal,
        currency: str,
        description: str | None = None,
        customer_gateway_id: str | None = None,
        payment_method_id: str | None = None,
        metadata: dict | None = None,
    ) -> GatewayResponse:
        """Crea un pago único."""
        ...

    @abstractmethod
    def get_payment_status(self, gateway_payment_id: str) -> GatewayResponse:
        """Consulta el estado actual de un pago en la pasarela."""
        ...

    # --- Suscripciones ---

    @abstractmethod
    def create_plan(
        self,
        name: str,
        amount: Decimal,
        currency: str,
        interval: str,
        interval_count: int = 1,
    ) -> GatewayResponse:
        """Crea un plan/precio de suscripción en la pasarela."""
        ...

    @abstractmethod
    def create_subscription(
        self,
        customer_gateway_id: str,
        plan_gateway_id: str,
        payment_method_id: str | None = None,
    ) -> GatewayResponse:
        """Suscribe un cliente a un plan."""
        ...

    @abstractmethod
    def cancel_subscription(self, gateway_subscription_id: str) -> GatewayResponse:
        """Cancela una suscripción activa."""
        ...

    # --- Reembolsos ---

    @abstractmethod
    def create_refund(
        self,
        gateway_payment_id: str,
        amount: Decimal | None = None,
        reason: str = "requested_by_customer",
    ) -> GatewayResponse:
        """Crea un reembolso (total si amount=None, parcial si se especifica)."""
        ...

    # --- Webhooks ---

    @abstractmethod
    def verify_webhook(self, payload: bytes, headers: dict) -> WebhookEvent:
        """Verifica la firma del webhook y parsea el evento.

        Raises:
            WebhookVerificationException: Si la firma es inválida.
        """
        ...
