from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    PostRequest,
    VariationsRequest,
    GeneratedPost,
    VariationsResponse,
    HistoryResponse,
    PlatformInfo,
    ErrorResponse,
)
from app.gemini_service import GeminiService
from app.prompts import PLATFORM_LIMITS

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida: inicializa el servicio de Gemini."""
    app.state.gemini_service = GeminiService()
    yield


app = FastAPI(
    title="🤖 API Generadora de Contenido",
    description=(
        "API REST para generar **posts de redes sociales** con inteligencia artificial.\n\n"
        "Genera contenido optimizado para **Twitter/X, Instagram, LinkedIn y Facebook** "
        "usando Google Gemini.\n\n"
        "### Características\n"
        "- Generación de posts optimizados por plataforma\n"
        "- Múltiples tonos de voz (profesional, casual, humorístico, inspiracional, educativo)\n"
        "- Soporte para español e inglés\n"
        "- Generación automática de hashtags\n"
        "- Múltiples variaciones de un mismo post\n"
        "- Historial de posts generados en la sesión\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    responses={
        401: {"model": ErrorResponse, "description": "API key inválida"},
        429: {"model": ErrorResponse, "description": "Límite de peticiones excedido"},
        503: {"model": ErrorResponse, "description": "Error de conexión con Gemini"},
    },
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────────────────────


@app.get("/", tags=["General"])
async def root():
    """Verifica el estado del servicio y muestra información general."""
    return {
        "status": "online",
        "service": "AI Content Generator",
        "provider": "Google Gemini",
        "model": settings.GEMINI_MODEL,
        "documentation": "/docs",
        "endpoints": {
            "generate_post": "POST /generate",
            "generate_variations": "POST /generate/variations",
            "history": "GET /history",
            "platforms": "GET /platforms",
        },
    }


# ─── Generación de Posts ─────────────────────────────────────────────────────


@app.post(
    "/generate",
    response_model=GeneratedPost,
    tags=["Generación"],
    summary="Generar un post",
    description=(
        "Genera un post único optimizado para la plataforma seleccionada. "
        "Personaliza el tono de voz, idioma y hashtags según tus necesidades."
    ),
)
async def generate_post(request: PostRequest):
    service: GeminiService = app.state.gemini_service
    return await service.generate_post(
        topic=request.topic,
        platform=request.platform,
        tone=request.tone,
        language=request.language,
        include_hashtags=request.include_hashtags,
    )


@app.post(
    "/generate/variations",
    response_model=VariationsResponse,
    tags=["Generación"],
    summary="Generar variaciones de un post",
    description=(
        "Genera múltiples variaciones de un post sobre el mismo tema. "
        "Cada variación usa un enfoque diferente manteniendo el mismo tono y plataforma."
    ),
)
async def generate_variations(request: VariationsRequest):
    service: GeminiService = app.state.gemini_service
    return await service.generate_variations(
        topic=request.topic,
        platform=request.platform,
        tone=request.tone,
        language=request.language,
        include_hashtags=request.include_hashtags,
        count=request.variations_count,
    )


# ─── Historial ───────────────────────────────────────────────────────────────


@app.get(
    "/history",
    response_model=HistoryResponse,
    tags=["Historial"],
    summary="Ver historial de posts",
    description="Lista todos los posts generados durante la sesión actual.",
)
async def get_history():
    service: GeminiService = app.state.gemini_service
    posts = service.get_history()
    return HistoryResponse(posts=posts, total=len(posts))


@app.delete(
    "/history",
    tags=["Historial"],
    summary="Limpiar historial",
    description="Elimina todos los posts del historial de la sesión actual.",
)
async def clear_history():
    service: GeminiService = app.state.gemini_service
    service.clear_history()
    return {"message": "Historial limpiado exitosamente", "total": 0}


# ─── Plataformas ─────────────────────────────────────────────────────────────


@app.get(
    "/platforms",
    response_model=list[PlatformInfo],
    tags=["Plataformas"],
    summary="Plataformas disponibles",
    description="Lista las plataformas de redes sociales soportadas con sus características.",
)
async def get_platforms():
    return [
        PlatformInfo(
            name=info["name"],
            key=key.value,
            max_characters=info["max_characters"],
            description=info["description"],
        )
        for key, info in PLATFORM_LIMITS.items()
    ]
