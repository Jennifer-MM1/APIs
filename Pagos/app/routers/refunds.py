import json
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.refund import Refund
from app.models.payment import Payment
from app.schemas.refund import RefundCreate, RefundResponse
from app.utils.exceptions import (
    PaymentNotFoundException,
    PaymentNotCompletedException,
    RefundExceedsAmountException,
)
from app.services.gateway_factory import get_gateway

router = APIRouter()


@router.post("/", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def create_refund(
    data: RefundCreate,
    db: Session = Depends(get_db),
):
    """Solicita un reembolso total o parcial de un pago completado.

    - Si `amount` es None, se reembolsa el monto total del pago.
    - Si se especifica `amount`, se hace un reembolso parcial.
    - Solo se pueden reembolsar pagos con estado `completed`.
    """
    # Verificar que el pago exista
    payment = db.query(Payment).filter(Payment.id == data.payment_id).first()
    if not payment:
        raise PaymentNotFoundException(data.payment_id)

    # Verificar que el pago esté completado
    if payment.status != "completed":
        raise PaymentNotCompletedException(data.payment_id, payment.status)

    # Determinar monto de reembolso
    refund_amount = data.amount if data.amount is not None else payment.amount

    # Calcular total ya reembolsado
    existing_refunds_total = (
        db.query(Refund)
        .filter(
            Refund.payment_id == data.payment_id,
            Refund.status.in_(["completed", "pending"]),
        )
        .with_entities(Refund.amount)
        .all()
    )
    total_refunded = sum(r.amount for r in existing_refunds_total)

    # Verificar que el reembolso no exceda el monto original
    remaining = Decimal(str(payment.amount)) - Decimal(str(total_refunded))
    if Decimal(str(refund_amount)) > remaining:
        raise RefundExceedsAmountException(
            float(refund_amount),
            float(remaining),
        )

    # Crear reembolso en la pasarela
    gw = get_gateway(payment.gateway)
    result = gw.create_refund(
        gateway_payment_id=payment.gateway_payment_id,
        amount=refund_amount,
        reason=data.reason.value,
    )

    # Guardar en base de datos local
    refund = Refund(
        payment_id=data.payment_id,
        gateway_refund_id=result.gateway_id,
        amount=refund_amount,
        reason=data.reason.value,
        status=result.status,
        notes=data.notes,
    )

    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


@router.get("/", response_model=list[RefundResponse])
def list_refunds(
    payment_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista reembolsos con filtro opcional por pago."""
    query = db.query(Refund)

    if payment_id:
        query = query.filter(Refund.payment_id == payment_id)

    refunds = query.order_by(Refund.created_at.desc()).offset(skip).limit(limit).all()
    return refunds


@router.get("/{refund_id}", response_model=RefundResponse)
def get_refund(
    refund_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de un reembolso."""
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        from app.utils.exceptions import PaymentNotFoundException
        raise PaymentNotFoundException(f"Reembolso {refund_id}")
    return refund
