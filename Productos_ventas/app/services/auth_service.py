from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.exceptions import ConflictException, NotFoundException


def register_user(db: Session, data: UserCreate) -> User:
    """Registra un nuevo usuario con contraseña hasheada."""
    # Verificar que el email no esté registrado
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise ConflictException(detail="El email ya está registrado")

    user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="customer",  # Por defecto todos son clientes
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserLogin) -> TokenResponse:
    """Autentica un usuario y retorna un token JWT."""
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise NotFoundException(detail="Email o contraseña incorrectos")

    if not user.is_active:
        raise NotFoundException(detail="Usuario inactivo")

    # Generar token JWT
    access_token = create_access_token(data={"sub": user.id})

    return TokenResponse(access_token=access_token)
