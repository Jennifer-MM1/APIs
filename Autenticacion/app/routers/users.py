from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument
from app.database import db
from app.schemas.user import UserOut
from app.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Usuarios"])

# Dependencia reutilizable para requerir rol de administrador
admin_required = RoleChecker(allowed_roles=["admin"])


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Retorna la información del usuario autenticado actual."""
    return UserOut.from_mongo(current_user)


@router.get("/", response_model=List[UserOut])
async def read_users(
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(admin_required),
):
    """Retorna la lista de todos los usuarios registrados (Solo Administradores)."""
    users_cursor = db.users.find().skip(skip).limit(limit)
    users_list = []
    async for user in users_cursor:
        users_list.append(UserOut.from_mongo(user))
    return users_list


@router.patch("/{username}/role", response_model=UserOut)
async def update_user_role(
    username: str,
    new_role: str,
    current_user: dict = Depends(admin_required),
):
    """Actualiza el rol de un usuario específico (Solo Administradores)."""
    # Validar roles permitidos
    if new_role not in ["admin", "editor", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol no permitido. Los roles válidos son: admin, editor, user",
        )

    # Actualizar en la colección de MongoDB
    updated_user = await db.users.find_one_and_update(
        {"username": username},
        {"$set": {"role": new_role}},
        return_document=ReturnDocument.AFTER,
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado",
        )

    return UserOut.from_mongo(updated_user)
