from typing import Optional
from jose import JWTError, jwt
from app.config import get_settings

settings = get_settings()


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un token JWT. Retorna None si es inválido.

    Usa la misma SECRET_KEY y ALGORITHM que la API de Autenticación
    para poder validar tokens emitidos por ese servicio.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
