from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.subscription import Subscription
from app.models.customer import Customer
from app.models.plan import Plan
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionBriefResponse
from app.utils.exceptions import (
    SubscriptionNotFoundException,
    CustomerNotFoundException,
    PlanNotFoundException,
    SubscriptionAlreadyCancelledException,
)
from app.utils.enums import SubscriptionStatus, GatewayEnum
from app.services.gateway_factory import get_gateway
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
):
    """Crea una nueva suscripción vinculando un cliente a un plan.

    - **Stripe**: Se crea inmediatamente si hay `payment_method_id`.
    - **PayPal/MercadoPago**: Se retorna `approval_url` para que el usuario apruebe.
    """
    # Verificar cliente
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise CustomerNotFoundException(data.customer_id)

    # Verificar plan
    plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
    if not plan:
        raise PlanNotFoundException(data.plan_id)

    # Obtener IDs del gateway
    customer_gw_id_map = {
        "stripe": customer.stripe_customer_id,
        "paypal": customer.paypal_customer_id or customer.email,
        "mercadopago": customer.mercadopago_customer_id or customer.email,
    }
    plan_gw_id_map = {
        "stripe": plan.stripe_price_id,
        "paypal": plan.paypal_plan_id,
        "mercadopago": plan.mercadopago_plan_id,
    }

    customer_gw_id = customer_gw_id_map.get(data.gateway.value)
    plan_gw_id = plan_gw_id_map.get(data.gateway.value)

    # Crear suscripción en la pasarela
    gw = get_gateway(data.gateway.value)
    result = gw.create_subscription(
        customer_gateway_id=customer_gw_id,
        plan_gateway_id=plan_gw_id,
        payment_method_id=data.payment_method_id,
    )

    # Guardar en base de datos local
    subscription = Subscription(
        customer_id=data.customer_id,
        plan_id=data.plan_id,
        gateway=data.gateway.value,
        gateway_subscription_id=result.gateway_id,
        status=result.status,
        current_period_start=datetime.utcnow(),
        approval_url=result.checkout_url,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.get("/", response_model=list[SubscriptionResponse])
def list_subscriptions(
    gateway: GatewayEnum | None = None,
    subscription_status: SubscriptionStatus | None = Query(None, alias="status"),
    customer_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista suscripciones con filtros opcionales."""
    query = db.query(Subscription)

    if gateway:
        query = query.filter(Subscription.gateway == gateway.value)
    if subscription_status:
        query = query.filter(Subscription.status == subscription_status.value)
    if customer_id:
        query = query.filter(Subscription.customer_id == customer_id)

    subscriptions = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de una suscripción."""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise SubscriptionNotFoundException(subscription_id)
    return subscription


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    """Cancela una suscripción activa."""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise SubscriptionNotFoundException(subscription_id)

    if subscription.status == "cancelled":
        raise SubscriptionAlreadyCancelledException(subscription_id)

    # Cancelar en la pasarela
    if subscription.gateway_subscription_id:
        try:
            gw = get_gateway(subscription.gateway)
            gw.cancel_subscription(subscription.gateway_subscription_id)
        except Exception:
            pass  # Continuar aunque falle la pasarela (marcar como cancelado localmente)

    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    db.commit()
    db.refresh(subscription)
    return subscription


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    """Pausa una suscripción activa (solo actualización local).

    Nota: No todas las pasarelas soportan pausa nativamente.
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise SubscriptionNotFoundException(subscription_id)

    if subscription.status == "cancelled":
        raise SubscriptionAlreadyCancelledException(subscription_id)

    subscription.status = "paused"
    db.commit()
    db.refresh(subscription)
    return subscription
