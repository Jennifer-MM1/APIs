from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user, require_admin
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderBriefResponse,
    OrderStatusUpdate,
)
from app.services import order_service
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crear un pedido — operación de venta.

    Valida stock, calcula totales con IVA 16%, descuenta inventario,
    y genera número de orden automático.
    """
    return order_service.create_order(db, data, current_user)


@router.get("/", response_model=List[OrderBriefResponse])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listar pedidos.
    - Clientes: solo sus propios pedidos.
    - Admins: todos los pedidos.
    """
    return order_service.get_user_orders(db, current_user, skip, limit, status)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener detalle completo de un pedido."""
    return order_service.get_order_by_id(db, order_id, current_user)


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Actualizar estado del pedido (solo admin).

    Transiciones válidas:
    - pending → confirmed, cancelled
    - confirmed → shipped, cancelled
    - shipped → delivered
    """
    return order_service.update_order_status(db, order_id, data.status, admin)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancelar un pedido y restaurar el stock al inventario.
    Solo pedidos en estado 'pending' o 'confirmed'.
    """
    return order_service.cancel_order(db, order_id, current_user)
