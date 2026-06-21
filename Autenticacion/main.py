from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, close_db
from app.routers import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación: inicialización y cierre de conexiones."""
    # Startup: Conectar a base de datos y crear índices
    await init_db()
    yield
    # Shutdown: Cerrar conexiones
    await close_db()


app = FastAPI(
    title="API de Autenticación y Autorización",
    description="Servicio de autenticación (Registro, Login, Tokens JWT) y roles/permisos con FastAPI y MongoDB Atlas.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración de CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los enrutadores
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/", tags=["General"])
async def root():
    """Ruta raíz para verificar la salud y el estado del servicio."""
    return {
        "status": "online",
        "service": "Authentication API",
        "database": "MongoDB Atlas",
        "documentation": "/docs",
    }
