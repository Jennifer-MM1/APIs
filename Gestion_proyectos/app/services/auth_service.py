from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.exceptions import ConflictException, UnauthorizedException


def register_user(db: Session, data: RegisterRequest) -> User:
    """Registra un nuevo usuario en la base de datos."""
    # Verificar si el username ya existe
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise ConflictException(detail="El nombre de usuario ya está en uso")

    # Verificar si el email ya existe
    existing_email = db.query(User).filter(User.email == data.email).first()
    if existing_email:
        raise ConflictException(detail="El email ya está registrado")

    # Crear usuario
    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, username: str, password: str) -> str:
    """Autentica un usuario y retorna un token JWT."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException(detail="Usuario o contraseña incorrectos")

    if not user.is_active:
        raise UnauthorizedException(detail="Usuario inactivo")

    # Crear token JWT
    access_token = create_access_token(data={"sub": user.id})
    return access_token
