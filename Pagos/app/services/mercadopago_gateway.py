import json
import uuid
from decimal import Decimal
import mercadopago
from app.config import Settings
from app.services.gateway_base import PaymentGateway, GatewayResponse, WebhookEvent
from app.utils.exceptions import PaymentGatewayException, WebhookVerificationException


class MercadoPagoGateway(PaymentGateway):
    """Implementación de MercadoPago usando el SDK oficial.

    MercadoPago tiene dos flujos principales:
    1. Pago directo (con token de tarjeta del frontend via MP.js)
    2. Checkout Pro (redirect — se crea una "preferencia" y el usuario paga en MP)

    Usamos Checkout Pro como flujo principal por ser más flexible.
    Para suscripciones usamos "preapprovals" (preaprobaciones).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    def _idempotency_headers(self) -> dict:
        """Genera headers con clave de idempotencia única."""
        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            "x-idempotency-key": str(uuid.uuid4()),
        }
        return request_options

    # --- Clientes ---

    def create_customer(self, email: str, full_name: str, **kwargs) -> GatewayResponse:
        """Crea un cliente en MercadoPago."""
        try:
            customer_data = {
                "email": email,
                "first_name": full_name.split(" ")[0],
                "last_name": " ".join(full_name.split(" ")[1:]) or full_name,
            }

            phone = kwargs.get("phone")
            if phone:
                customer_data["phone"] = {"number": phone}

            result = self.sdk.customer().create(customer_data)
            response = result.get("response", {})

            if result.get("status") in [200, 201]:
                return GatewayResponse(
                    success=True,
                    gateway_id=str(response.get("id")),
                    status="active",
                    raw_response=response,
                )
            else:
                raise PaymentGatewayException(
                    "mercadopago",
                    response.get("message", "Error al crear cliente"),
                )
        except PaymentGatewayException:
            raise
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

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
        """Crea una preferencia de pago (Checkout Pro).

        Retorna un `checkout_url` para redirigir al usuario a MercadoPago.
        Cuando el usuario paga, MP notifica via webhook.
        """
        try:
            preference_data = {
                "items": [
                    {
                        "title": description or "Pago",
                        "quantity": 1,
                        "unit_price": float(amount),
                        "currency_id": currency.upper(),
                    }
                ],
                "back_urls": {
                    "success": "https://example.com/payment/success",
                    "failure": "https://example.com/payment/failure",
                    "pending": "https://example.com/payment/pending",
                },
                "auto_return": "approved",
                "metadata": metadata or {},
            }

            if customer_gateway_id:
                preference_data["payer"] = {"id": customer_gateway_id}

            result = self.sdk.preference().create(preference_data)
            response = result.get("response", {})

            if result.get("status") in [200, 201]:
                # Usar sandbox URL en modo test, live URL en producción
                checkout_url = response.get("sandbox_init_point") or response.get("init_point")

                return GatewayResponse(
                    success=True,
                    gateway_id=str(response.get("id")),
                    status="pending",
                    checkout_url=checkout_url,
                    raw_response=response,
                )
            else:
                raise PaymentGatewayException(
                    "mercadopago",
                    response.get("message", "Error al crear preferencia de pago"),
                )
        except PaymentGatewayException:
            raise
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

    def get_payment_status(self, gateway_payment_id: str) -> GatewayResponse:
        """Consulta el estado de un pago en MercadoPago."""
        try:
            result = self.sdk.payment().get(gateway_payment_id)
            response = result.get("response", {})

            status_map = {
                "pending": "pending",
                "approved": "completed",
                "authorized": "processing",
                "in_process": "processing",
                "in_mediation": "processing",
                "rejected": "failed",
                "cancelled": "cancelled",
                "refunded": "completed",  # El pago fue reembolsado
                "charged_back": "failed",
            }

            return GatewayResponse(
                success=True,
                gateway_id=str(response.get("id")),
                status=status_map.get(response.get("status", ""), "pending"),
                raw_response=response,
            )
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

    # --- Suscripciones ---

    def create_plan(
        self,
        name: str,
        amount: Decimal,
        currency: str,
        interval: str,
        interval_count: int = 1,
    ) -> GatewayResponse:
        """Crea un plan de suscripción (preapproval_plan) en MercadoPago.

        MercadoPago usa 'preapprovals' para suscripciones recurrentes.
        """
        try:
            # Mapear intervalos a MercadoPago
            frequency_map = {
                "week": {"frequency": interval_count * 7, "frequency_type": "days"},
                "month": {"frequency": interval_count, "frequency_type": "months"},
                "year": {"frequency": interval_count * 12, "frequency_type": "months"},
            }

            freq = frequency_map.get(interval, {"frequency": 1, "frequency_type": "months"})

            plan_data = {
                "reason": name,
                "auto_recurring": {
                    "frequency": freq["frequency"],
                    "frequency_type": freq["frequency_type"],
                    "transaction_amount": float(amount),
                    "currency_id": currency.upper(),
                },
                "back_url": "https://example.com/subscription/callback",
            }

            result = self.sdk.preapproval_plan().create(plan_data)
            response = result.get("response", {})

            if result.get("status") in [200, 201]:
                return GatewayResponse(
                    success=True,
                    gateway_id=str(response.get("id")),
                    status="active",
                    raw_response=response,
                )
            else:
                raise PaymentGatewayException(
                    "mercadopago",
                    response.get("message", "Error al crear plan"),
                )
        except PaymentGatewayException:
            raise
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

    def create_subscription(
        self,
        customer_gateway_id: str,
        plan_gateway_id: str,
        payment_method_id: str | None = None,
    ) -> GatewayResponse:
        """Crea una suscripción (preapproval) vinculada a un plan."""
        try:
            sub_data = {
                "preapproval_plan_id": plan_gateway_id,
                "payer_email": customer_gateway_id,  # Usamos email del cliente
                "back_url": "https://example.com/subscription/callback",
            }

            result = self.sdk.preapproval().create(sub_data)
            response = result.get("response", {})

            if result.get("status") in [200, 201]:
                checkout_url = response.get("sandbox_init_point") or response.get("init_point")

                return GatewayResponse(
                    success=True,
                    gateway_id=str(response.get("id")),
                    status="pending",
                    checkout_url=checkout_url,
                    raw_response=response,
                )
            else:
                raise PaymentGatewayException(
                    "mercadopago",
                    response.get("message", "Error al crear suscripción"),
                )
        except PaymentGatewayException:
            raise
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

    def cancel_subscription(self, gateway_subscription_id: str) -> GatewayResponse:
        """Cancela una suscripción (preapproval) en MercadoPago."""
        try:
            result = self.sdk.preapproval().update(
                gateway_subscription_id,
                {"status": "cancelled"},
            )
            response = result.get("response", {})

            return GatewayResponse(
                success=True,
                gateway_id=gateway_subscription_id,
                status="cancelled",
                raw_response=response,
            )
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

    # --- Reembolsos ---

    def create_refund(
        self,
        gateway_payment_id: str,
        amount: Decimal | None = None,
        reason: str = "requested_by_customer",
    ) -> GatewayResponse:
        """Crea un reembolso en MercadoPago.

        Puede ser total (sin amount) o parcial (con amount).
        """
        try:
            refund_data = {}
            if amount is not None:
                refund_data["amount"] = float(amount)

            result = self.sdk.refund().create(
                gateway_payment_id,
                refund_data,
                self._idempotency_headers(),
            )
            response = result.get("response", {})

            if result.get("status") in [200, 201]:
                return GatewayResponse(
                    success=True,
                    gateway_id=str(response.get("id")),
                    status="completed",
                    raw_response=response,
                )
            else:
                raise PaymentGatewayException(
                    "mercadopago",
                    response.get("message", "Error al crear reembolso"),
                )
        except PaymentGatewayException:
            raise
        except Exception as e:
            raise PaymentGatewayException("mercadopago", str(e))

    # --- Webhooks ---

    def verify_webhook(self, payload: bytes, headers: dict) -> WebhookEvent:
        """Parsea un webhook de MercadoPago.

        MercadoPago envía notificaciones IPN con el tipo de evento
        y el ID del recurso afectado. Se puede verificar consultando
        el recurso directamente.
        """
        try:
            body = json.loads(payload)

            # MercadoPago puede enviar diferentes formatos
            event_type = body.get("type") or body.get("topic", "")
            action = body.get("action", "")
            data = body.get("data", {})

            # Determinar el event_type normalizado
            if action:
                event_type = f"{event_type}.{action}"

            resource_id = data.get("id")

            return WebhookEvent(
                event_id=str(body.get("id", "")),
                event_type=event_type,
                gateway="mercadopago",
                resource_id=str(resource_id) if resource_id else None,
                data=body,
            )
        except (json.JSONDecodeError, KeyError):
            raise WebhookVerificationException("mercadopago")
