from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import db
from app.models.user import UserInDB
from app.schemas.user import UserCreate, UserOut, Token
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    """Registra un nuevo usuario en la base de datos MongoDB."""
    # Verificar si el usuario o email ya están registrados
    existing_user = await db.users.find_one(
        {
            "$or": [
                {"username": user_in.username},
                {"email": user_in.email},
            ]
        }
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o correo electrónico ya están registrados",
        )

    # Crear el usuario en la base de datos
    hashed_pw = hash_password(user_in.password)
    user_db = UserInDB(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=user_in.role or "user",
    )

    # Guardar en base de datos MongoDB
    result = await db.users.insert_one(user_db.to_mongo())

    # Recuperar el documento creado para retornarlo como respuesta
    new_user = await db.users.find_one({"_id": result.inserted_id})
    return UserOut.from_mongo(new_user)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Inicia sesión validando credenciales de OAuth2 y retorna un JWT."""
    # Buscar el usuario por username en la colección de MongoDB
    user = await db.users.find_one({"username": form_data.username})

    # Verificar existencia y contraseña
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar si la cuenta está activa
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de usuario está inactiva",
        )

    # Generar el token de acceso JWT
    token_data = {"sub": user["username"], "role": user.get("role", "user")}
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}
