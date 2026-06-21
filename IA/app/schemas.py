from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


# ─── Enums ───────────────────────────────────────────────────────────────────


class Platform(str, Enum):
    """Plataformas de redes sociales soportadas."""

    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class Tone(str, Enum):
    """Tonos de voz disponibles para la generación de contenido."""

    PROFESIONAL = "profesional"
    CASUAL = "casual"
    HUMORISTICO = "humorístico"
    INSPIRACIONAL = "inspiracional"
    EDUCATIVO = "educativo"


# ─── Request Models ─────────────────────────────────────────────────────────


class PostRequest(BaseModel):
    """Solicitud para generar un post de redes sociales."""

    topic: str = Field(
        ...,
        description="Tema o idea principal del post",
        min_length=3,
        max_length=500,
        examples=["Lanzamiento de nuestra nueva app de productividad"],
    )
    platform: Platform = Field(
        ...,
        description="Red social destino del post",
        examples=["twitter"],
    )
    tone: Tone = Field(
        default=Tone.PROFESIONAL,
        description="Tono de voz del contenido",
        examples=["profesional"],
    )
    language: str = Field(
        default="es",
        description="Idioma del post (es = español, en = inglés)",
        pattern="^(es|en)$",
        examples=["es"],
    )
    include_hashtags: bool = Field(
        default=True,
        description="Incluir hashtags relevantes",
    )


class VariationsRequest(PostRequest):
    """Solicitud para generar múltiples variaciones de un post."""

    variations_count: int = Field(
        default=3,
        description="Número de variaciones a generar",
        ge=1,
        le=5,
    )


# ─── Response Models ────────────────────────────────────────────────────────


class GeneratedPost(BaseModel):
    """Un post generado por la IA."""

    content: str = Field(description="Contenido del post generado")
    platform: Platform = Field(description="Red social destino")
    tone: Tone = Field(description="Tono de voz utilizado")
    hashtags: list[str] = Field(
        default_factory=list,
        description="Lista de hashtags generados",
    )
    character_count: int = Field(description="Cantidad de caracteres del post")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha y hora de generación",
    )


class VariationsResponse(BaseModel):
    """Respuesta con múltiples variaciones de un post."""

    topic: str = Field(description="Tema solicitado")
    platform: Platform = Field(description="Red social destino")
    tone: Tone = Field(description="Tono de voz utilizado")
    variations: list[GeneratedPost] = Field(
        description="Lista de variaciones generadas"
    )
    total_variations: int = Field(description="Total de variaciones generadas")


class HistoryResponse(BaseModel):
    """Respuesta con el historial de posts generados."""

    posts: list[GeneratedPost] = Field(description="Posts generados en la sesión")
    total: int = Field(description="Total de posts en el historial")


class PlatformInfo(BaseModel):
    """Información sobre una plataforma soportada."""

    name: str = Field(description="Nombre de la plataforma")
    key: str = Field(description="Clave identificadora")
    max_characters: int | None = Field(
        description="Límite de caracteres (null si no aplica)"
    )
    description: str = Field(description="Descripción del tipo de contenido")


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada."""

    detail: str = Field(description="Descripción del error")
    error_code: str = Field(description="Código de error interno")
