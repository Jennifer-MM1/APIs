from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserInDB(BaseModel):
    """Representa la estructura del documento de Usuario guardado en MongoDB."""

    username: str
    email: str
    hashed_password: str
    full_name: str
    role: str = "user"  # "admin", "editor", "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_mongo(self) -> dict:
        """Convierte el modelo a un diccionario listo para MongoDB."""
        return self.model_dump()
