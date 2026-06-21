from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Construir URL de conexión a la base de datos.
#
# Turso (libSQL) es 100% compatible con SQLite. La API soporta dos modos:
#
# 1. LOCAL (desarrollo): SQLite estándar — sin dependencias extra.
#    DATABASE_URL = "sqlite:///pagos.db"
#
# 2. TURSO (producción): Requiere el paquete `sqlalchemy-libsql`.
#    DATABASE_URL = "sqlite+libsql://tu-db.turso.io?secure=true"
#    Se necesita TURSO_AUTH_TOKEN para autenticación.
#
# Ambos usan el mismo SQL y los mismos modelos SQLAlchemy.

database_url = settings.DATABASE_URL

# Configurar argumentos de conexión
connect_args = {}

if database_url.startswith("sqlite:///") or database_url.startswith("sqlite:"):
    # Modo SQLite local — necesita check_same_thread=False para FastAPI
    connect_args["check_same_thread"] = False
elif settings.TURSO_AUTH_TOKEN:
    # Modo Turso remoto — pasar token de autenticación
    connect_args["auth_token"] = settings.TURSO_AUTH_TOKEN

# Motor de conexión
engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=False,
)

# Sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Clase base para los modelos
class Base(DeclarativeBase):
    pass
