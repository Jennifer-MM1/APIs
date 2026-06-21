import json
import hashlib
import hmac
from decimal import Decimal
import httpx
from app.config import Settings
from app.services.gateway_base import PaymentGateway, GatewayResponse, WebhookEvent
from app.utils.exceptions import PaymentGatewayException, WebhookVerificationException


class PayPalGateway(PaymentGateway):
    """Implementación de PayPal usando la Orders API v2 directamente con httpx.

    El SDK viejo (paypalrestsdk) está deprecado. Usamos la API REST directamente:
    - Pagos: Orders API v2 (crear orden → redirect → capturar)
    - Suscripciones: Billing API v1 (planes + suscripciones)
    - Reembolsos: Payments API v2 (captures/{id}/refund)
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.paypal_base_url
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self._access_token: str | None = None

    def _get_access_token(self) -> str:
        """Obtiene un OAuth2 access token de PayPal."""
        if self._access_token:
            return self._access_token

        try:
            response = httpx.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token
        except httpx.HTTPError as e:
            raise PaymentGatewayException("paypal", f"Error de autenticación: {str(e)}")

    def _headers(self) -> dict:
        """Headers de autorización para las peticiones a PayPal."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Ejecuta una petición HTTP a la API de PayPal."""
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                **kwargs,
            )
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("message", str(e))
            except Exception:
                error_detail = str(e)
            raise PaymentGatewayException("paypal", error_detail)
        except httpx.HTTPError as e:
            raise PaymentGatewayException("paypal", str(e))

    # --- Clientes ---

    def create_customer(self, email: str, full_name: str, **kwargs) -> GatewayResponse:
        """PayPal no tiene un endpoint formal de 'crear cliente'.

        Retornamos el email como identificador — PayPal identifica
        pagadores por su email/cuenta de PayPal al momento del pago.
        """
        return GatewayResponse(
            success=True,
            gateway_id=email,  # Usamos email como referencia
            status="active",
            raw_response={"email": email, "name": full_name},
        )

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
        """Crea una orden de pago en PayPal (Orders API v2).

        El flujo de PayPal es redirect-based:
        1. Backend crea la orden → recibe links
        2. Frontend redirige al usuario a `approve` link
        3. Usuario aprueba → PayPal redirige de vuelta
        4. Backend captura la orden
        """
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency.upper(),
                        "value": str(amount),
                    },
                }
            ],
        }

        if description:
            order_data["purchase_units"][0]["description"] = description

        data = self._request("POST", "/v2/checkout/orders", json=order_data)

        # Extraer URL de aprobación
        checkout_url = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                checkout_url = link["href"]
                break

        status_map = {
            "CREATED": "pending",
            "SAVED": "pending",
            "APPROVED": "processing",
            "VOIDED": "cancelled",
            "COMPLETED": "completed",
            "PAYER_ACTION_REQUIRED": "pending",
        }

        return GatewayResponse(
            success=True,
            gateway_id=data.get("id"),
            status=status_map.get(data.get("status", ""), "pending"),
            checkout_url=checkout_url,
            raw_response=data,
        )

    def capture_payment(self, order_id: str) -> GatewayResponse:
        """Captura una orden aprobada por el usuario."""
        data = self._request("POST", f"/v2/checkout/orders/{order_id}/capture")

        return GatewayResponse(
            success=True,
            gateway_id=data.get("id"),
            status="completed" if data.get("status") == "COMPLETED" else "processing",
            raw_response=data,
        )

    def get_payment_status(self, gateway_payment_id: str) -> GatewayResponse:
        """Consulta el estado de una orden."""
        data = self._request("GET", f"/v2/checkout/orders/{gateway_payment_id}")

        status_map = {
            "CREATED": "pending",
            "SAVED": "pending",
            "APPROVED": "processing",
            "VOIDED": "cancelled",
            "COMPLETED": "completed",
        }

        return GatewayResponse(
            success=True,
            gateway_id=data.get("id"),
            status=status_map.get(data.get("status", ""), "pending"),
            raw_response=data,
        )

    # --- Suscripciones ---

    def create_plan(
        self,
        name: str,
        amount: Decimal,
        currency: str,
        interval: str,
        interval_count: int = 1,
    ) -> GatewayResponse:
        """Crea un producto y plan de facturación en PayPal Billing API."""
        # Primero crear el producto (catálogo)
        product_data = {
            "name": name,
            "type": "SERVICE",
        }
        product = self._request("POST", "/v1/catalogs/products", json=product_data)

        # Mapear intervalos a PayPal
        interval_map = {
            "week": "WEEK",
            "month": "MONTH",
            "year": "YEAR",
        }

        # Luego crear el plan de facturación
        plan_data = {
            "product_id": product["id"],
            "name": name,
            "billing_cycles": [
                {
                    "frequency": {
                        "interval_unit": interval_map.get(interval, "MONTH"),
                        "interval_count": interval_count,
                    },
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,  # Infinito
                    "pricing_scheme": {
                        "fixed_price": {
                            "value": str(amount),
                            "currency_code": currency.upper(),
                        }
                    },
                }
            ],
            "payment_preferences": {
                "auto_bill_outstanding": True,
                "payment_failure_threshold": 3,
            },
        }

        plan = self._request("POST", "/v1/billing/plans", json=plan_data)

        return GatewayResponse(
            success=True,
            gateway_id=plan.get("id"),
            status="active" if plan.get("status") == "ACTIVE" else "pending",
            raw_response={"product": product, "plan": plan},
        )

    def create_subscription(
        self,
        customer_gateway_id: str,
        plan_gateway_id: str,
        payment_method_id: str | None = None,
    ) -> GatewayResponse:
        """Crea una suscripción en PayPal (requiere aprobación del usuario)."""
        sub_data = {
            "plan_id": plan_gateway_id,
            "subscriber": {
                "email_address": customer_gateway_id,  # En PayPal, usamos email
            },
            "application_context": {
                "return_url": "https://example.com/subscription/success",
                "cancel_url": "https://example.com/subscription/cancel",
            },
        }

        data = self._request("POST", "/v1/billing/subscriptions", json=sub_data)

        # Extraer URL de aprobación
        approval_url = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link["href"]
                break

        return GatewayResponse(
            success=True,
            gateway_id=data.get("id"),
            status="pending",  # Necesita aprobación del usuario
            checkout_url=approval_url,
            raw_response=data,
        )

    def cancel_subscription(self, gateway_subscription_id: str) -> GatewayResponse:
        """Cancela una suscripción en PayPal."""
        self._request(
            "POST",
            f"/v1/billing/subscriptions/{gateway_subscription_id}/cancel",
            json={"reason": "Cancelado por el usuario"},
        )

        return GatewayResponse(
            success=True,
            gateway_id=gateway_subscription_id,
            status="cancelled",
            raw_response={"id": gateway_subscription_id, "status": "CANCELLED"},
        )

    # --- Reembolsos ---

    def create_refund(
        self,
        gateway_payment_id: str,
        amount: Decimal | None = None,
        reason: str = "requested_by_customer",
    ) -> GatewayResponse:
        """Crea un reembolso en PayPal.

        Necesita el `capture_id` (no el order_id). Si recibimos un order_id,
        primero lo consultamos para obtener el capture_id.
        """
        # Intentar obtener el capture_id si el ID parece ser una orden
        capture_id = gateway_payment_id
        try:
            order = self._request("GET", f"/v2/checkout/orders/{gateway_payment_id}")
            # Extraer el primer capture_id de las purchase_units
            for unit in order.get("purchase_units", []):
                for capture in unit.get("payments", {}).get("captures", []):
                    capture_id = capture["id"]
                    break
        except PaymentGatewayException:
            pass  # Asumimos que ya es un capture_id

        refund_data = {}
        if amount is not None:
            refund_data["amount"] = {
                "value": str(amount),
                "currency_code": "MXN",
            }
        if reason:
            refund_data["note_to_payer"] = reason

        data = self._request(
            "POST",
            f"/v2/payments/captures/{capture_id}/refund",
            json=refund_data if refund_data else None,
        )

        status_map = {
            "COMPLETED": "completed",
            "PENDING": "pending",
            "FAILED": "failed",
        }

        return GatewayResponse(
            success=True,
            gateway_id=data.get("id"),
            status=status_map.get(data.get("status", ""), "pending"),
            raw_response=data,
        )

    # --- Webhooks ---

    def verify_webhook(self, payload: bytes, headers: dict) -> WebhookEvent:
        """Verifica un webhook de PayPal.

        PayPal envía headers de verificación que se pueden validar
        contra su API de verificación de webhooks.
        """
        try:
            body = json.loads(payload)

            # Verificación simplificada — en producción usar la API de verificación
            # POST /v1/notifications/verify-webhook-signature
            event_type = body.get("event_type", "")
            resource = body.get("resource", {})

            return WebhookEvent(
                event_id=body.get("id", ""),
                event_type=event_type,
                gateway="paypal",
                resource_id=resource.get("id"),
                data=resource,
            )
        except (json.JSONDecodeError, KeyError):
            raise WebhookVerificationException("paypal")
