from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services import auth_service
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario."""
    user = auth_service.register_user(db, data)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Iniciar sesión y obtener token JWT.

    Usa el formato OAuth2:
    - username: nombre de usuario
    - password: contraseña
    """
    access_token = auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Obtener el perfil del usuario autenticado."""
    return current_user
