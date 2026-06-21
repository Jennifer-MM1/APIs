from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Recurso no encontrado (404)."""

    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    """Conflicto — recurso ya existe (409)."""

    def __init__(self, detail: str = "El recurso ya existe"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InsufficientStockException(HTTPException):
    """Stock insuficiente para completar la operación (400)."""

    def __init__(self, product_name: str, available: int, requested: int):
        detail = (
            f"Stock insuficiente para '{product_name}': "
            f"disponible={available}, solicitado={requested}"
        )
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidOperationException(HTTPException):
    """Operación no válida (400)."""

    def __init__(self, detail: str = "Operación no válida"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ForbiddenException(HTTPException):
    """Acceso denegado (403)."""

    def __init__(self, detail: str = "No tienes permisos para realizar esta acción"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
