from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.user import UserResponse, UserUpdate
from app.services import user_service
from app.models.user import User
from app.utils.exceptions import ForbiddenException

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar todos los usuarios (requiere autenticación)."""
    return user_service.get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener un usuario por su ID."""
    return user_service.get_user_by_id(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar un usuario (solo el propio usuario puede actualizarse)."""
    if current_user.id != user_id:
        raise ForbiddenException(detail="Solo puedes actualizar tu propio perfil")
    return user_service.update_user(db, user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar un usuario (solo el propio usuario puede eliminarse)."""
    if current_user.id != user_id:
        raise ForbiddenException(detail="Solo puedes eliminar tu propia cuenta")
    user_service.delete_user(db, user_id)
