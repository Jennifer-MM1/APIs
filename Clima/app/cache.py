from cachetools import TTLCache
from app.config import get_settings

settings = get_settings()

# Cache en memoria con TTL configurable
# maxsize=256: máximo 256 entradas cacheadas
_cache = TTLCache(maxsize=256, ttl=settings.CACHE_TTL_SECONDS)


def get_cache_key(endpoint: str, **params) -> str:
    """Genera una clave única para el cache basada en el endpoint y parámetros."""
    sorted_params = sorted(params.items())
    params_str = "&".join(f"{k}={v}" for k, v in sorted_params if v is not None)
    return f"{endpoint}:{params_str}"


def get_cached(key: str):
    """Obtiene un valor del cache. Retorna None si no existe o expiró."""
    return _cache.get(key)


def set_cached(key: str, value) -> None:
    """Almacena un valor en el cache con TTL automático."""
    _cache[key] = value


def clear_cache() -> None:
    """Limpia todo el cache."""
    _cache.clear()


def cache_info() -> dict:
    """Retorna información del estado actual del cache."""
    return {
        "current_size": len(_cache),
        "max_size": _cache.maxsize,
        "ttl_seconds": int(_cache.ttl),
    }
