from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db, require_admin
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services import product_service
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    category_id: int | None = Query(None, description="Filtrar por categoría"),
    brand: str | None = Query(None, description="Filtrar por marca"),
    min_price: Decimal | None = Query(None, description="Precio mínimo"),
    max_price: Decimal | None = Query(None, description="Precio máximo"),
    db: Session = Depends(get_db),
):
    """Listar productos con filtros opcionales."""
    return product_service.get_all_products(
        db, skip, limit, category_id, brand, min_price, max_price
    )


@router.get("/search", response_model=List[ProductResponse])
def search_products(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Buscar productos por nombre o descripción."""
    return product_service.search_products(db, q, skip, limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Obtener detalle de un producto (incluye stock disponible)."""
    return product_service.get_product_by_id(db, product_id)


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Crear un nuevo producto con inventario inicial (solo admin)."""
    return product_service.create_product(db, data)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Actualizar un producto (solo admin)."""
    return product_service.update_product(db, product_id, data)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Desactivar un producto — soft delete (solo admin)."""
    product_service.delete_product(db, product_id)
