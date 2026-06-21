"""
Templates de prompts optimizados para cada plataforma de redes sociales.

Cada función retorna un prompt diseñado para que Gemini genere contenido
específico y de alta calidad para la plataforma indicada.
"""

from app.schemas import Platform, Tone


# ─── Límites de caracteres por plataforma ────────────────────────────────────

PLATFORM_LIMITS: dict[str, dict] = {
    Platform.TWITTER: {
        "name": "Twitter / X",
        "max_characters": 280,
        "description": "Posts cortos y directos, máximo 280 caracteres",
    },
    Platform.INSTAGRAM: {
        "name": "Instagram",
        "max_characters": 2200,
        "description": "Captions atractivos con emojis y hasta 30 hashtags",
    },
    Platform.LINKEDIN: {
        "name": "LinkedIn",
        "max_characters": 3000,
        "description": "Contenido profesional con formato y saltos de línea",
    },
    Platform.FACEBOOK: {
        "name": "Facebook",
        "max_characters": 63206,
        "description": "Posts cercanos y conversacionales con llamados a la acción",
    },
}


# ─── Mapeo de tonos a descripciones ──────────────────────────────────────────

TONE_DESCRIPTIONS: dict[str, str] = {
    Tone.PROFESIONAL: "profesional, serio y confiable. Usa un lenguaje formal pero accesible",
    Tone.CASUAL: "casual, relajado y amigable. Usa un lenguaje coloquial y cercano",
    Tone.HUMORISTICO: "divertido y con humor inteligente. Usa juegos de palabras y referencias populares",
    Tone.INSPIRACIONAL: "motivador e inspiracional. Usa frases poderosas que inviten a la acción",
    Tone.EDUCATIVO: "educativo e informativo. Comparte datos interesantes y conocimiento de valor",
}


def _language_instruction(language: str) -> str:
    """Retorna la instrucción de idioma para el prompt."""
    if language == "en":
        return "Write the entire post in English."
    return "Escribe todo el post en español."


# ─── Prompt principal ────────────────────────────────────────────────────────


def build_prompt(
    topic: str,
    platform: Platform,
    tone: Tone,
    language: str = "es",
    include_hashtags: bool = True,
    variation_index: int | None = None,
) -> str:
    """
    Construye el prompt optimizado para generar un post.

    Args:
        topic: Tema o idea del post.
        platform: Red social destino.
        tone: Tono de voz deseado.
        language: Código de idioma (es/en).
        include_hashtags: Si se deben incluir hashtags.
        variation_index: Índice de variación (para generar contenido diferente).

    Returns:
        Prompt formateado listo para enviar a Gemini.
    """
    platform_info = PLATFORM_LIMITS[platform]
    tone_desc = TONE_DESCRIPTIONS[tone]
    lang_instruction = _language_instruction(language)

    hashtag_instruction = ""
    if include_hashtags:
        if platform == Platform.INSTAGRAM:
            hashtag_instruction = (
                "Genera entre 10 y 20 hashtags relevantes y populares. "
                "Incluye una mezcla de hashtags populares y de nicho."
            )
        elif platform == Platform.TWITTER:
            hashtag_instruction = (
                "Genera entre 2 y 4 hashtags relevantes. "
                "Recuerda que los hashtags cuentan dentro del límite de 280 caracteres."
            )
        else:
            hashtag_instruction = "Genera entre 3 y 7 hashtags relevantes."
    else:
        hashtag_instruction = "NO incluyas hashtags."

    variation_instruction = ""
    if variation_index is not None:
        variation_instruction = (
            f"\n\nEsta es la variación #{variation_index + 1}. "
            "Genera contenido COMPLETAMENTE DIFERENTE a las otras variaciones. "
            "Usa un enfoque, estructura y estilo distintos para abordar el mismo tema."
        )

    platform_specific = _get_platform_instructions(platform)

    return f"""Eres un experto en marketing digital y creación de contenido para redes sociales.
Tu tarea es generar un post de alta calidad para {platform_info['name']}.

## Tema del post
{topic}

## Instrucciones de plataforma
- Plataforma: {platform_info['name']}
- Límite de caracteres: {platform_info['max_characters']}
- {platform_specific}

## Tono de voz
El tono debe ser {tone_desc}.

## Idioma
{lang_instruction}

## Hashtags
{hashtag_instruction}
{variation_instruction}

## FORMATO DE RESPUESTA (OBLIGATORIO)
Responde ÚNICAMENTE con un JSON válido, sin markdown ni texto adicional.
El JSON debe tener esta estructura exacta:
{{
    "content": "El texto del post aquí (SIN incluir los hashtags en este campo)",
    "hashtags": ["#hashtag1", "#hashtag2"]
}}

REGLAS IMPORTANTES:
- El campo "content" debe contener SOLO el texto del post, SIN hashtags.
- Los hashtags van ÚNICAMENTE en el array "hashtags".
- Si no se pidieron hashtags, el array debe estar vacío: []
- El contenido NO debe exceder {platform_info['max_characters']} caracteres.
- NO agregues explicaciones, solo el JSON.
"""


def _get_platform_instructions(platform: Platform) -> str:
    """Retorna instrucciones específicas según la plataforma."""
    instructions = {
        Platform.TWITTER: (
            "El post DEBE tener máximo 280 caracteres (incluyendo espacios y emojis). "
            "Sé conciso y directo. Usa 1-2 emojis estratégicamente. "
            "El mensaje debe ser impactante y fácil de retuitear."
        ),
        Platform.INSTAGRAM: (
            "Crea un caption atractivo y visualmente organizado. "
            "Usa emojis para separar secciones. "
            "Incluye un llamado a la acción (ej: 'Guarda este post', 'Comenta tu opinión'). "
            "Usa saltos de línea para mejorar la legibilidad."
        ),
        Platform.LINKEDIN: (
            "Crea un post profesional con formato estructurado. "
            "Comienza con un hook que capture la atención (primera línea es clave). "
            "Usa saltos de línea y viñetas para organizar ideas. "
            "Incluye una reflexión o llamado a la acción al final. "
            "Evita emojis excesivos, máximo 2-3 relevantes."
        ),
        Platform.FACEBOOK: (
            "Crea un post cercano y conversacional. "
            "Haz una pregunta al final para fomentar la interacción. "
            "Usa emojis con moderación (3-5). "
            "El post debe sentirse personal y auténtico."
        ),
    }
    return instructions.get(platform, "")
