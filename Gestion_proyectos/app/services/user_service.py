from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserUpdate
from app.utils.exceptions import NotFoundException, ConflictException


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Obtiene todos los usuarios con paginación."""
    return db.query(User).offset(skip).limit(limit).all()


def get_user_by_id(db: Session, user_id: int) -> User:
    """Obtiene un usuario por su ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(detail=f"Usuario con ID {user_id} no encontrado")
    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    """Actualiza los datos de un usuario."""
    user = get_user_by_id(db, user_id)

    # Verificar email único si se está actualizando
    if data.email and data.email != user.email:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ConflictException(detail="El email ya está registrado por otro usuario")

    # Actualizar solo los campos proporcionados
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    """Elimina un usuario."""
    user = get_user_by_id(db, user_id)
    db.delete(user)
    db.commit()
