from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    GEMINI_API_KEY: str = "tu_api_key_aqui"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    DEFAULT_LANG: str = "es"
    MAX_HISTORY: int = 50

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Retorna la instancia cacheada de Settings."""
    return Settings()
