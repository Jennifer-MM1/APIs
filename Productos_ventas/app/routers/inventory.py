from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user, require_admin
from app.schemas.inventory import (
    InventoryResponse,
    InventoryUpdate,
    InventoryWithProductResponse,
    RestockRequest,
)
from app.services import inventory_service
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[InventoryWithProductResponse])
def list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Listar inventario completo con datos de producto (solo admin)."""
    return inventory_service.get_all_inventory(db, skip, limit)


@router.get("/low-stock", response_model=List[InventoryWithProductResponse])
def get_low_stock(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Obtener productos con stock bajo (stock ≤ min_stock) (solo admin)."""
    return inventory_service.get_low_stock_products(db)


@router.get("/{product_id}", response_model=InventoryResponse)
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener el stock de un producto específico."""
    return inventory_service.get_inventory_by_product(db, product_id)


@router.put("/{product_id}", response_model=InventoryResponse)
def update_inventory(
    product_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Actualizar stock y/o umbral mínimo (solo admin)."""
    return inventory_service.update_inventory(db, product_id, data)


@router.post("/{product_id}/restock", response_model=InventoryResponse)
def restock(
    product_id: int,
    data: RestockRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Registrar restock — agrega cantidad al stock actual (solo admin)."""
    return inventory_service.restock_product(db, product_id, data.quantity)
