from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Excepción para recursos no encontrados (404)."""

    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    """Excepción para acceso denegado (403)."""

    def __init__(self, detail: str = "No tienes permisos para realizar esta acción"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedException(HTTPException):
    """Excepción para autenticación fallida (401)."""

    def __init__(self, detail: str = "No autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class BadRequestException(HTTPException):
    """Excepción para solicitudes inválidas (400)."""

    def __init__(self, detail: str = "Solicitud inválida"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictException(HTTPException):
    """Excepción para conflictos de datos (409)."""

    def __init__(self, detail: str = "El recurso ya existe"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
