from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db, require_admin
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithChildrenResponse,
)
from app.schemas.product import ProductResponse
from app.services import category_service, product_service
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    only_parents: bool = Query(False, description="Solo categorías raíz (sin padre)"),
    db: Session = Depends(get_db),
):
    """Listar todas las categorías."""
    return category_service.get_all_categories(db, skip, limit, only_parents)


@router.get("/{category_id}", response_model=CategoryWithChildrenResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Obtener detalle de una categoría con sus subcategorías."""
    return category_service.get_category_by_id(db, category_id)


@router.get("/{category_id}/products", response_model=List[ProductResponse])
def get_category_products(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Obtener los productos de una categoría."""
    return product_service.get_products_by_category(db, category_id, skip, limit)


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Crear una nueva categoría (solo admin)."""
    return category_service.create_category(db, data)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Actualizar una categoría (solo admin)."""
    return category_service.update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Eliminar una categoría (solo admin)."""
    category_service.delete_category(db, category_id)
