from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema para iniciar sesión."""

    username: str
    password: str


class RegisterRequest(BaseModel):
    """Schema para registrar un nuevo usuario."""

    username: str
    email: str
    password: str
    full_name: str


class TokenResponse(BaseModel):
    """Schema de respuesta con el token JWT."""

    access_token: str
    token_type: str = "bearer"
