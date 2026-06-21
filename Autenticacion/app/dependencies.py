from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database import db
from app.utils.security import decode_access_token

# El tokenUrl apunta al endpoint que maneja la autenticación y devuelve el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db():
    """Retorna la instancia de base de datos activa."""
    return db


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependencia para validar el token JWT y obtener el usuario actual."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Buscar el usuario en la base de datos de MongoDB
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo",
        )

    return user


class RoleChecker:
    """Clase para validar que el usuario tenga uno de los roles permitidos."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción",
            )
        return current_user
