from typing import List
from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.exceptions import NotFoundException, ConflictException, InvalidOperationException


def get_all_categories(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    only_parents: bool = False,
) -> List[Category]:
    """Obtiene todas las categorías con paginación. Si only_parents=True, solo las raíz."""
    query = db.query(Category)
    if only_parents:
        query = query.filter(Category.parent_id.is_(None))
    return query.offset(skip).limit(limit).all()


def get_category_by_id(db: Session, category_id: int) -> Category:
    """Obtiene una categoría por su ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise NotFoundException(detail=f"Categoría con ID {category_id} no encontrada")
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    """Crea una nueva categoría."""
    # Verificar nombre único
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise ConflictException(detail=f"Ya existe una categoría con el nombre '{data.name}'")

    # Verificar que la categoría padre existe si se especificó
    if data.parent_id:
        parent = db.query(Category).filter(Category.id == data.parent_id).first()
        if not parent:
            raise NotFoundException(detail=f"Categoría padre con ID {data.parent_id} no encontrada")

    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    """Actualiza una categoría existente."""
    category = get_category_by_id(db, category_id)

    # Verificar nombre único si se cambia
    if data.name and data.name != category.name:
        existing = db.query(Category).filter(Category.name == data.name).first()
        if existing:
            raise ConflictException(detail=f"Ya existe una categoría con el nombre '{data.name}'")

    # Verificar que no se asigne como padre de sí misma
    if data.parent_id and data.parent_id == category_id:
        raise InvalidOperationException(detail="Una categoría no puede ser padre de sí misma")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    """Elimina una categoría (y sus subcategorías en cascada)."""
    category = get_category_by_id(db, category_id)

    # Verificar que no tenga productos activos
    if category.products:
        raise InvalidOperationException(
            detail=f"No se puede eliminar la categoría '{category.name}' porque tiene {len(category.products)} producto(s) asociado(s)"
        )

    db.delete(category)
    db.commit()
