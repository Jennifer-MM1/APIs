"""
Servicio de comunicación con Google Gemini.

Encapsula toda la lógica de generación de contenido usando la API de Gemini,
incluyendo manejo de errores y parseo de respuestas.
"""

import json
import logging
from datetime import datetime

from google import genai
from fastapi import HTTPException

from app.config import get_settings
from app.schemas import (
    GeneratedPost,
    Platform,
    Tone,
    VariationsResponse,
)
from app.prompts import build_prompt

logger = logging.getLogger(__name__)


class GeminiService:
    """Servicio para generar contenido de redes sociales con Google Gemini."""

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self.history: list[GeneratedPost] = []
        self.max_history = settings.MAX_HISTORY

    async def generate_post(
        self,
        topic: str,
        platform: Platform,
        tone: Tone = Tone.PROFESIONAL,
        language: str = "es",
        include_hashtags: bool = True,
    ) -> GeneratedPost:
        """
        Genera un post único para la plataforma indicada.

        Args:
            topic: Tema del post.
            platform: Red social destino.
            tone: Tono de voz.
            language: Idioma (es/en).
            include_hashtags: Incluir hashtags.

        Returns:
            GeneratedPost con el contenido generado.

        Raises:
            HTTPException: Si ocurre un error con la API de Gemini.
        """
        prompt = build_prompt(
            topic=topic,
            platform=platform,
            tone=tone,
            language=language,
            include_hashtags=include_hashtags,
        )

        raw_response = await self._call_gemini(prompt)
        post = self._parse_response(raw_response, platform, tone)

        # Agregar al historial
        self._add_to_history(post)

        return post

    async def generate_variations(
        self,
        topic: str,
        platform: Platform,
        tone: Tone = Tone.PROFESIONAL,
        language: str = "es",
        include_hashtags: bool = True,
        count: int = 3,
    ) -> VariationsResponse:
        """
        Genera múltiples variaciones de un post.

        Args:
            topic: Tema del post.
            platform: Red social destino.
            tone: Tono de voz.
            language: Idioma (es/en).
            include_hashtags: Incluir hashtags.
            count: Número de variaciones (1-5).

        Returns:
            VariationsResponse con todas las variaciones.
        """
        variations: list[GeneratedPost] = []

        for i in range(count):
            prompt = build_prompt(
                topic=topic,
                platform=platform,
                tone=tone,
                language=language,
                include_hashtags=include_hashtags,
                variation_index=i,
            )
            raw_response = await self._call_gemini(prompt)
            post = self._parse_response(raw_response, platform, tone)
            variations.append(post)
            self._add_to_history(post)

        return VariationsResponse(
            topic=topic,
            platform=platform,
            tone=tone,
            variations=variations,
            total_variations=len(variations),
        )

    async def _call_gemini(self, prompt: str) -> str:
        """
        Llama a la API de Gemini y retorna la respuesta en texto.

        Raises:
            HTTPException: Con código apropiado según el tipo de error.
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            if not response.text:
                raise HTTPException(
                    status_code=500,
                    detail="Gemini no generó contenido. Intenta con otro tema.",
                )

            return response.text

        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Error al llamar a Gemini: {e}")

            if "api_key" in error_msg or "unauthorized" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="API key de Gemini inválida o no configurada. "
                    "Verifica tu GEMINI_API_KEY en el archivo .env",
                )
            elif "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
                raise HTTPException(
                    status_code=429,
                    detail="Se excedió el límite de peticiones a Gemini. "
                    "Espera un momento e intenta de nuevo.",
                )
            elif "not found" in error_msg or "404" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Modelo de Gemini no encontrado. Verifica GEMINI_MODEL en .env",
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Error de conexión con Gemini: {str(e)}",
                )

    def _parse_response(
        self,
        raw_text: str,
        platform: Platform,
        tone: Tone,
    ) -> GeneratedPost:
        """
        Parsea la respuesta JSON de Gemini a un GeneratedPost.

        Si el parseo falla, usa el texto crudo como contenido del post.
        """
        # Limpiar posible markdown del response
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
            content = data.get("content", clean_text)
            hashtags = data.get("hashtags", [])
        except (json.JSONDecodeError, AttributeError):
            logger.warning("No se pudo parsear JSON de Gemini, usando texto crudo")
            content = clean_text
            hashtags = []

        return GeneratedPost(
            content=content,
            platform=platform,
            tone=tone,
            hashtags=hashtags,
            character_count=len(content),
            created_at=datetime.now(),
        )

    def _add_to_history(self, post: GeneratedPost) -> None:
        """Agrega un post al historial, respetando el límite máximo."""
        self.history.append(post)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def get_history(self) -> list[GeneratedPost]:
        """Retorna el historial de posts generados."""
        return self.history

    def clear_history(self) -> None:
        """Limpia el historial de posts."""
        self.history.clear()
