from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    OPENWEATHER_API_KEY: str = "tu_api_key_aqui"
    CACHE_TTL_SECONDS: int = 600
    DEFAULT_LANG: str = "es"
    DEFAULT_UNITS: str = "metric"

    # URL base de la API de OpenWeatherMap
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Retorna la instancia cacheada de Settings."""
    return Settings()
