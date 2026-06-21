from fastapi import HTTPException, status


class PaymentGatewayException(HTTPException):
    """Error de comunicación con la pasarela de pago."""

    def __init__(self, gateway: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error en pasarela '{gateway}': {detail}",
        )


class PaymentNotFoundException(HTTPException):
    """Pago no encontrado (404)."""

    def __init__(self, payment_id: int | str = ""):
        detail = f"Pago no encontrado: {payment_id}" if payment_id else "Pago no encontrado"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class CustomerNotFoundException(HTTPException):
    """Cliente no encontrado (404)."""

    def __init__(self, customer_id: int | str = ""):
        detail = (
            f"Cliente no encontrado: {customer_id}"
            if customer_id
            else "Cliente no encontrado"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PlanNotFoundException(HTTPException):
    """Plan de suscripción no encontrado (404)."""

    def __init__(self, plan_id: int | str = ""):
        detail = f"Plan no encontrado: {plan_id}" if plan_id else "Plan no encontrado"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class SubscriptionNotFoundException(HTTPException):
    """Suscripción no encontrada (404)."""

    def __init__(self, subscription_id: int | str = ""):
        detail = (
            f"Suscripción no encontrada: {subscription_id}"
            if subscription_id
            else "Suscripción no encontrada"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvalidGatewayException(HTTPException):
    """Gateway no configurado o no existe (400)."""

    def __init__(self, gateway: str, available: list[str]):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Gateway '{gateway}' no está disponible. "
                f"Gateways configurados: {', '.join(available) or 'ninguno'}"
            ),
        )


class WebhookVerificationException(HTTPException):
    """Firma de webhook inválida (400)."""

    def __init__(self, gateway: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verificación de webhook fallida para '{gateway}'",
        )


class RefundExceedsAmountException(HTTPException):
    """Monto de reembolso excede el pago original (400)."""

    def __init__(self, refund_amount: float, original_amount: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El monto del reembolso ({refund_amount}) excede "
                f"el monto original del pago ({original_amount})"
            ),
        )


class SubscriptionAlreadyCancelledException(HTTPException):
    """La suscripción ya fue cancelada (400)."""

    def __init__(self, subscription_id: int | str = ""):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La suscripción {subscription_id} ya fue cancelada",
        )


class DuplicateWebhookException(HTTPException):
    """Evento webhook ya fue procesado (200 — idempotente)."""

    def __init__(self, event_id: str):
        super().__init__(
            status_code=status.HTTP_200_OK,
            detail=f"Evento ya procesado: {event_id}",
        )


class PaymentNotCompletedException(HTTPException):
    """El pago no está completado, no se puede reembolsar (400)."""

    def __init__(self, payment_id: int | str, current_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El pago {payment_id} tiene estado '{current_status}'. "
                f"Solo se pueden reembolsar pagos con estado 'completed'"
            ),
        )


class ConflictException(HTTPException):
    """Conflicto — recurso ya existe (409)."""

    def __init__(self, detail: str = "El recurso ya existe"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
