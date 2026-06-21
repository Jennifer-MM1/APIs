import json
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.webhook_event import WebhookEvent
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.gateway_factory import get_gateway
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _process_webhook_event(event_type: str, resource_id: str | None, gateway: str, db: Session):
    """Procesa un evento de webhook actualizando el estado en la DB local.

    Mapea los tipos de eventos de cada pasarela a acciones locales.
    """
    if not resource_id:
        return

    # --- Eventos de pago ---
    payment_completed_events = [
        "payment_intent.succeeded",        # Stripe
        "CHECKOUT.ORDER.COMPLETED",        # PayPal
        "PAYMENT.CAPTURE.COMPLETED",       # PayPal
        "payment.updated",                 # MercadoPago
        "payment.created",                 # MercadoPago
    ]

    payment_failed_events = [
        "payment_intent.payment_failed",   # Stripe
        "PAYMENT.CAPTURE.DENIED",          # PayPal
    ]

    # --- Eventos de suscripción ---
    subscription_cancelled_events = [
        "customer.subscription.deleted",   # Stripe
        "BILLING.SUBSCRIPTION.CANCELLED",  # PayPal
        "subscription_preapproval.updated", # MercadoPago
    ]

    subscription_active_events = [
        "customer.subscription.updated",    # Stripe
        "BILLING.SUBSCRIPTION.ACTIVATED",   # PayPal
    ]

    # Buscar y actualizar pago
    if event_type in payment_completed_events:
        payment = (
            db.query(Payment)
            .filter(Payment.gateway_payment_id == resource_id)
            .first()
        )
        if payment:
            # Para MercadoPago, verificar el estado real consultando la pasarela
            if gateway == "mercadopago":
                try:
                    gw = get_gateway(gateway)
                    result = gw.get_payment_status(resource_id)
                    payment.status = result.status
                except Exception:
                    payment.status = "completed"
            else:
                payment.status = "completed"

    elif event_type in payment_failed_events:
        payment = (
            db.query(Payment)
            .filter(Payment.gateway_payment_id == resource_id)
            .first()
        )
        if payment:
            payment.status = "failed"

    # Buscar y actualizar suscripción
    elif event_type in subscription_cancelled_events:
        sub = (
            db.query(Subscription)
            .filter(Subscription.gateway_subscription_id == resource_id)
            .first()
        )
        if sub:
            sub.status = "cancelled"
            from datetime import datetime
            sub.cancelled_at = datetime.utcnow()

    elif event_type in subscription_active_events:
        sub = (
            db.query(Subscription)
            .filter(Subscription.gateway_subscription_id == resource_id)
            .first()
        )
        if sub:
            sub.status = "active"

    db.commit()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Recibe y procesa eventos webhook de Stripe.

    Stripe firma sus webhooks con HMAC — verificamos la firma antes de procesar.
    """
    payload = await request.body()
    headers = dict(request.headers)

    # Verificar firma y parsear evento
    gw = get_gateway("stripe")
    event = gw.verify_webhook(payload, headers)

    # Chequear idempotencia
    existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event.event_id).first()
    if existing:
        return {"status": "already_processed", "event_id": event.event_id}

    # Guardar evento
    webhook_event = WebhookEvent(
        gateway="stripe",
        event_id=event.event_id,
        event_type=event.event_type,
        payload=json.dumps(event.data, default=str),
        processed=True,
    )
    db.add(webhook_event)

    # Procesar el evento
    _process_webhook_event(event.event_type, event.resource_id, "stripe", db)

    db.commit()
    return {"status": "processed", "event_id": event.event_id}


@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Recibe y procesa eventos webhook de PayPal."""
    payload = await request.body()
    headers = dict(request.headers)

    gw = get_gateway("paypal")
    event = gw.verify_webhook(payload, headers)

    # Chequear idempotencia
    existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event.event_id).first()
    if existing:
        return {"status": "already_processed", "event_id": event.event_id}

    # Guardar evento
    webhook_event = WebhookEvent(
        gateway="paypal",
        event_id=event.event_id,
        event_type=event.event_type,
        payload=json.dumps(event.data, default=str),
        processed=True,
    )
    db.add(webhook_event)

    # Procesar
    _process_webhook_event(event.event_type, event.resource_id, "paypal", db)

    db.commit()
    return {"status": "processed", "event_id": event.event_id}


@router.post("/mercadopago")
async def mercadopago_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Recibe y procesa eventos webhook de MercadoPago."""
    payload = await request.body()
    headers = dict(request.headers)

    gw = get_gateway("mercadopago")
    event = gw.verify_webhook(payload, headers)

    # Chequear idempotencia
    event_id = event.event_id or f"mp-{event.resource_id}"
    existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
    if existing:
        return {"status": "already_processed", "event_id": event_id}

    # Guardar evento
    webhook_event = WebhookEvent(
        gateway="mercadopago",
        event_id=event_id,
        event_type=event.event_type,
        payload=json.dumps(event.data, default=str),
        processed=True,
    )
    db.add(webhook_event)

    # Procesar
    _process_webhook_event(event.event_type, event.resource_id, "mercadopago", db)

    db.commit()
    return {"status": "processed", "event_id": event_id}
