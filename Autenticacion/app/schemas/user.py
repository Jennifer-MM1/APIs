from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Esquema de entrada para el registro de un nuevo usuario."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: Optional[str] = "user"  # Opciones comunes: "admin", "editor", "user"


class UserOut(BaseModel):
    """Esquema de salida para retornar los datos del usuario sin contraseñas ni detalles de DB."""

    id: str
    username: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, data: dict) -> Optional["UserOut"]:
        """Convierte un documento crudo de MongoDB a UserOut."""
        if not data:
            return None
        data_copy = data.copy()
        # Convertimos _id de ObjectId a str y lo guardamos como 'id'
        data_copy["id"] = str(data_copy.pop("_id"))
        return cls(**data_copy)


class Token(BaseModel):
    """Esquema de salida para el token de acceso generado."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Datos codificados dentro de los claims del token JWT."""

    username: Optional[str] = None
    role: Optional[str] = None
