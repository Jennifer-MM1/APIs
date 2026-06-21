import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentBriefResponse, PaymentListResponse
from app.utils.exceptions import PaymentNotFoundException, CustomerNotFoundException
from app.utils.enums import PaymentStatus, GatewayEnum
from app.services.gateway_factory import get_gateway
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _generate_payment_number() -> str:
    """Genera un número de pago único: PAY-YYYYMMDD-XXXXXX"""
    now = datetime.utcnow()
    import uuid
    short_id = uuid.uuid4().hex[:6].upper()
    return f"PAY-{now.strftime('%Y%m%d')}-{short_id}"


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
):
    """Crea un nuevo pago.

    Flujo según la pasarela:
    - **Stripe**: Si se envía `payment_method_id`, el pago se confirma inmediatamente.
      Si no, se crea un PaymentIntent pendiente.
    - **PayPal**: Se crea una orden y se retorna `checkout_url` para redirect del usuario.
    - **MercadoPago**: Se crea una preferencia y se retorna `checkout_url` (Checkout Pro).
    """
    # Verificar que el cliente exista
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise CustomerNotFoundException(data.customer_id)

    # Obtener el ID del cliente en la pasarela seleccionada
    customer_gw_id_map = {
        "stripe": customer.stripe_customer_id,
        "paypal": customer.paypal_customer_id,
        "mercadopago": customer.mercadopago_customer_id,
    }
    customer_gateway_id = customer_gw_id_map.get(data.gateway.value)

    # Crear el pago en la pasarela
    gw = get_gateway(data.gateway.value)
    result = gw.create_payment(
        amount=data.amount,
        currency=data.currency.value,
        description=data.description,
        customer_gateway_id=customer_gateway_id,
        payment_method_id=data.payment_method_id,
        metadata=data.metadata,
    )

    # Guardar en base de datos local
    payment = Payment(
        payment_number=_generate_payment_number(),
        customer_id=data.customer_id,
        gateway=data.gateway.value,
        gateway_payment_id=result.gateway_id,
        amount=data.amount,
        currency=data.currency.value,
        status=result.status,
        description=data.description,
        metadata_json=json.dumps(data.metadata) if data.metadata else None,
        gateway_response=json.dumps(result.raw_response, default=str),
        checkout_url=result.checkout_url,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/", response_model=PaymentListResponse)
def list_payments(
    gateway: GatewayEnum | None = None,
    payment_status: PaymentStatus | None = Query(None, alias="status"),
    customer_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista pagos con filtros opcionales por gateway, estado y cliente."""
    query = db.query(Payment)

    if gateway:
        query = query.filter(Payment.gateway == gateway.value)
    if payment_status:
        query = query.filter(Payment.status == payment_status.value)
    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    total = query.count()
    payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()

    return PaymentListResponse(total=total, payments=payments)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de un pago por su ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise PaymentNotFoundException(payment_id)
    return payment


@router.post("/{payment_id}/capture", response_model=PaymentResponse)
def capture_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    """Captura un pago aprobado por el usuario (flujo redirect de PayPal/MercadoPago).

    Después de que el usuario aprueba el pago en la pasarela,
    este endpoint finaliza la transacción.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise PaymentNotFoundException(payment_id)

    if payment.gateway == "paypal" and payment.gateway_payment_id:
        from app.services.paypal_gateway import PayPalGateway
        gw = get_gateway("paypal")
        # PayPalGateway tiene el método capture_payment adicional
        if isinstance(gw, PayPalGateway):
            result = gw.capture_payment(payment.gateway_payment_id)
            payment.status = result.status
            payment.gateway_response = json.dumps(result.raw_response, default=str)
    else:
        # Para otros gateways, consultamos el estado actual
        gw = get_gateway(payment.gateway)
        if payment.gateway_payment_id:
            result = gw.get_payment_status(payment.gateway_payment_id)
            payment.status = result.status

    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/sync", response_model=PaymentResponse)
def sync_payment_status(
    payment_id: int,
    db: Session = Depends(get_db),
):
    """Sincroniza el estado de un pago con la pasarela externa.

    Útil para verificar manualmente si un pago cambió de estado.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise PaymentNotFoundException(payment_id)

    if payment.gateway_payment_id:
        gw = get_gateway(payment.gateway)
        result = gw.get_payment_status(payment.gateway_payment_id)
        payment.status = result.status
        db.commit()
        db.refresh(payment)

    return payment
