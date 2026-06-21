from typing import List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import InventoryUpdate, InventoryWithProductResponse
from app.utils.exceptions import NotFoundException, InvalidOperationException


def get_inventory_by_product(db: Session, product_id: int) -> Inventory:
    """Obtiene el inventario de un producto."""
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inventory:
        raise NotFoundException(detail=f"Inventario para producto con ID {product_id} no encontrado")
    return inventory


def get_all_inventory(db: Session, skip: int = 0, limit: int = 100) -> List[InventoryWithProductResponse]:
    """Obtiene el inventario completo con datos del producto."""
    inventories = (
        db.query(Inventory)
        .options(joinedload(Inventory.product))
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for inv in inventories:
        result.append(
            InventoryWithProductResponse(
                id=inv.id,
                product_id=inv.product_id,
                stock=inv.stock,
                min_stock=inv.min_stock,
                last_restock=inv.last_restock,
                updated_at=inv.updated_at,
                product_name=inv.product.name,
                product_sku=inv.product.sku,
                is_low_stock=inv.stock <= inv.min_stock,
            )
        )
    return result


def update_inventory(db: Session, product_id: int, data: InventoryUpdate) -> Inventory:
    """Actualiza el stock y/o umbral mínimo de un producto."""
    inventory = get_inventory_by_product(db, product_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inventory, field, value)

    db.commit()
    db.refresh(inventory)
    return inventory


def restock_product(db: Session, product_id: int, quantity: int) -> Inventory:
    """Agrega stock a un producto (restock)."""
    if quantity <= 0:
        raise InvalidOperationException(detail="La cantidad de restock debe ser mayor a 0")

    inventory = get_inventory_by_product(db, product_id)
    inventory.stock += quantity
    inventory.last_restock = datetime.utcnow()

    db.commit()
    db.refresh(inventory)
    return inventory


def get_low_stock_products(db: Session) -> List[InventoryWithProductResponse]:
    """Obtiene productos con stock igual o inferior al mínimo."""
    inventories = (
        db.query(Inventory)
        .options(joinedload(Inventory.product))
        .all()
    )

    result = []
    for inv in inventories:
        if inv.stock <= inv.min_stock:
            result.append(
                InventoryWithProductResponse(
                    id=inv.id,
                    product_id=inv.product_id,
                    stock=inv.stock,
                    min_stock=inv.min_stock,
                    last_restock=inv.last_restock,
                    updated_at=inv.updated_at,
                    product_name=inv.product.name,
                    product_sku=inv.product.sku,
                    is_low_stock=True,
                )
            )
    return result
