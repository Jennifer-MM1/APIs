from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, projects, tasks

app = FastAPI(
    title="API Gestión de Proyectos",
    description="API REST para gestión de proyectos, tareas y usuarios con autenticación JWT y roles.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - Permite conexiones desde apps web y móviles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Usuarios"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Proyectos"])
app.include_router(tasks.router, prefix="/api/v1/projects", tags=["Tareas"])


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "API de Gestión de Proyectos",
        "version": "1.0.0",
        "docs": "/docs",
    }
