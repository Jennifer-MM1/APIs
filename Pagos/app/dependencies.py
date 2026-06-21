from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.security import decode_access_token

# Esquema OAuth2 para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db() -> Generator:
    """Dependencia que provee una sesión de base de datos (Turso/libSQL)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
) -> dict | None:
    """Dependencia opcional — retorna el payload del JWT o None si no hay token.

    Útil para endpoints que pueden funcionar con o sin autenticación.
    """
    if token is None:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    return payload


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """Dependencia que extrae y valida el usuario actual del token JWT.

    Retorna el payload del JWT (sub, email, role, etc.) — no consulta
    la base de datos local ya que los usuarios están en la API de Autenticación.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    return payload


def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependencia que verifica que el usuario actual sea administrador."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user
