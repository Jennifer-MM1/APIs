from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.exceptions import NotFoundException, ConflictException


def get_all_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_id: int | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    is_active: bool | None = True,
) -> List[Product]:
    """Obtiene productos con filtros opcionales."""
    query = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.inventory),
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    return query.offset(skip).limit(limit).all()


def search_products(db: Session, query_text: str, skip: int = 0, limit: int = 50) -> List[Product]:
    """Busca productos por nombre o descripción."""
    return (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.inventory))
        .filter(
            (Product.name.ilike(f"%{query_text}%"))
            | (Product.description.ilike(f"%{query_text}%"))
        )
        .filter(Product.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_product_by_id(db: Session, product_id: int) -> Product:
    """Obtiene un producto por su ID con sus relaciones."""
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.inventory))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise NotFoundException(detail=f"Producto con ID {product_id} no encontrado")
    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    """Crea un nuevo producto y su registro de inventario inicial."""
    # Verificar SKU único
    existing = db.query(Product).filter(Product.sku == data.sku).first()
    if existing:
        raise ConflictException(detail=f"Ya existe un producto con el SKU '{data.sku}'")

    # Verificar que la categoría existe
    category = db.query(Category).filter(Category.id == data.category_id).first()
    if not category:
        raise NotFoundException(detail=f"Categoría con ID {data.category_id} no encontrada")

    # Crear producto (excluir campos de inventario)
    product_data = data.model_dump(exclude={"initial_stock", "min_stock"})
    product = Product(**product_data)
    db.add(product)
    db.flush()  # Obtener el ID sin hacer commit

    # Crear registro de inventario automáticamente
    inventory = Inventory(
        product_id=product.id,
        stock=data.initial_stock,
        min_stock=data.min_stock,
    )
    db.add(inventory)

    db.commit()
    db.refresh(product)

    # Cargar relaciones para la respuesta
    return get_product_by_id(db, product.id)


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    """Actualiza un producto existente."""
    product = get_product_by_id(db, product_id)

    # Verificar SKU único si se cambia
    if data.sku and data.sku != product.sku:
        existing = db.query(Product).filter(Product.sku == data.sku).first()
        if existing:
            raise ConflictException(detail=f"Ya existe un producto con el SKU '{data.sku}'")

    # Verificar categoría si se cambia
    if data.category_id:
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise NotFoundException(detail=f"Categoría con ID {data.category_id} no encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return get_product_by_id(db, product.id)


def delete_product(db: Session, product_id: int) -> None:
    """Desactiva un producto (soft delete para preservar historial de pedidos)."""
    product = get_product_by_id(db, product_id)
    product.is_active = False
    db.commit()


def get_products_by_category(db: Session, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
    """Obtiene productos de una categoría específica."""
    # Verificar que la categoría existe
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise NotFoundException(detail=f"Categoría con ID {category_id} no encontrada")

    return (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.inventory))
        .filter(Product.category_id == category_id, Product.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
