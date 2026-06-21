import json
from decimal import Decimal
import stripe
from app.config import Settings
from app.services.gateway_base import PaymentGateway, GatewayResponse, WebhookEvent
from app.utils.exceptions import PaymentGatewayException, WebhookVerificationException


class StripeGateway(PaymentGateway):
    """Implementación de Stripe usando el SDK oficial.

    Stripe maneja los pagos de forma directa (server-side):
    - El frontend obtiene un `payment_method_id` con Stripe.js
    - El backend crea un PaymentIntent con ese method
    - El pago se confirma inmediatamente (si no requiere 3DS)
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        stripe.api_key = settings.STRIPE_SECRET_KEY

    # --- Clientes ---

    def create_customer(self, email: str, full_name: str, **kwargs) -> GatewayResponse:
        """Crea un cliente en Stripe."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=full_name,
                metadata=kwargs.get("metadata", {}),
            )
            return GatewayResponse(
                success=True,
                gateway_id=customer.id,
                status="active",
                raw_response=dict(customer),
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    # --- Pagos ---

    def create_payment(
        self,
        amount: Decimal,
        currency: str,
        description: str | None = None,
        customer_gateway_id: str | None = None,
        payment_method_id: str | None = None,
        metadata: dict | None = None,
    ) -> GatewayResponse:
        """Crea un PaymentIntent en Stripe.

        Stripe requiere montos en centavos (enteros).
        Ej: $100.50 MXN → 10050
        """
        try:
            # Stripe usa montos en centavos
            amount_cents = int(amount * 100)

            params = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "metadata": metadata or {},
            }

            if description:
                params["description"] = description

            if customer_gateway_id:
                params["customer"] = customer_gateway_id

            if payment_method_id:
                params["payment_method"] = payment_method_id
                params["confirm"] = True
                params["automatic_payment_methods"] = {
                    "enabled": True,
                    "allow_redirects": "never",
                }
            else:
                params["automatic_payment_methods"] = {"enabled": True}

            intent = stripe.PaymentIntent.create(**params)

            # Mapear estado de Stripe a nuestro enum
            status_map = {
                "requires_payment_method": "pending",
                "requires_confirmation": "pending",
                "requires_action": "processing",
                "processing": "processing",
                "requires_capture": "processing",
                "canceled": "cancelled",
                "succeeded": "completed",
            }

            return GatewayResponse(
                success=True,
                gateway_id=intent.id,
                status=status_map.get(intent.status, "pending"),
                raw_response=dict(intent),
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    def get_payment_status(self, gateway_payment_id: str) -> GatewayResponse:
        """Consulta el estado de un PaymentIntent."""
        try:
            intent = stripe.PaymentIntent.retrieve(gateway_payment_id)
            status_map = {
                "requires_payment_method": "pending",
                "requires_confirmation": "pending",
                "requires_action": "processing",
                "processing": "processing",
                "requires_capture": "processing",
                "canceled": "cancelled",
                "succeeded": "completed",
            }
            return GatewayResponse(
                success=True,
                gateway_id=intent.id,
                status=status_map.get(intent.status, "pending"),
                raw_response=dict(intent),
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    # --- Suscripciones ---

    def create_plan(
        self,
        name: str,
        amount: Decimal,
        currency: str,
        interval: str,
        interval_count: int = 1,
    ) -> GatewayResponse:
        """Crea un Product + Price en Stripe (equivale a un 'plan')."""
        try:
            # Stripe separa Product (qué vendes) y Price (cuánto cuesta)
            product = stripe.Product.create(name=name)

            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(amount * 100),
                currency=currency.lower(),
                recurring={
                    "interval": interval,
                    "interval_count": interval_count,
                },
            )
            return GatewayResponse(
                success=True,
                gateway_id=price.id,  # Guardamos el Price ID
                status="active",
                raw_response={"product": dict(product), "price": dict(price)},
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    def create_subscription(
        self,
        customer_gateway_id: str,
        plan_gateway_id: str,
        payment_method_id: str | None = None,
    ) -> GatewayResponse:
        """Crea una suscripción en Stripe."""
        try:
            params = {
                "customer": customer_gateway_id,
                "items": [{"price": plan_gateway_id}],
            }

            if payment_method_id:
                params["default_payment_method"] = payment_method_id

            subscription = stripe.Subscription.create(**params)

            status_map = {
                "active": "active",
                "past_due": "past_due",
                "canceled": "cancelled",
                "incomplete": "pending",
                "incomplete_expired": "expired",
                "trialing": "active",
                "unpaid": "past_due",
                "paused": "paused",
            }

            return GatewayResponse(
                success=True,
                gateway_id=subscription.id,
                status=status_map.get(subscription.status, "pending"),
                raw_response=dict(subscription),
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    def cancel_subscription(self, gateway_subscription_id: str) -> GatewayResponse:
        """Cancela una suscripción en Stripe."""
        try:
            subscription = stripe.Subscription.cancel(gateway_subscription_id)
            return GatewayResponse(
                success=True,
                gateway_id=subscription.id,
                status="cancelled",
                raw_response=dict(subscription),
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    # --- Reembolsos ---

    def create_refund(
        self,
        gateway_payment_id: str,
        amount: Decimal | None = None,
        reason: str = "requested_by_customer",
    ) -> GatewayResponse:
        """Crea un reembolso en Stripe."""
        try:
            params = {"payment_intent": gateway_payment_id}

            if amount is not None:
                params["amount"] = int(amount * 100)

            # Mapear razón a las que acepta Stripe
            reason_map = {
                "requested_by_customer": "requested_by_customer",
                "duplicate": "duplicate",
                "fraudulent": "fraudulent",
            }
            if reason in reason_map:
                params["reason"] = reason_map[reason]

            refund = stripe.Refund.create(**params)

            status_map = {
                "succeeded": "completed",
                "pending": "pending",
                "failed": "failed",
                "canceled": "failed",
            }

            return GatewayResponse(
                success=True,
                gateway_id=refund.id,
                status=status_map.get(refund.status, "pending"),
                raw_response=dict(refund),
            )
        except stripe.StripeError as e:
            raise PaymentGatewayException("stripe", str(e))

    # --- Webhooks ---

    def verify_webhook(self, payload: bytes, headers: dict) -> WebhookEvent:
        """Verifica y parsea un webhook de Stripe usando la firma."""
        try:
            sig_header = headers.get("stripe-signature", "")
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.settings.STRIPE_WEBHOOK_SECRET,
            )

            # Extraer ID del recurso principal
            resource_id = None
            if event.data and event.data.object:
                resource_id = event.data.object.get("id")

            return WebhookEvent(
                event_id=event.id,
                event_type=event.type,
                gateway="stripe",
                resource_id=resource_id,
                data=dict(event.data.object) if event.data else {},
            )
        except (stripe.SignatureVerificationError, ValueError):
            raise WebhookVerificationException("stripe")
