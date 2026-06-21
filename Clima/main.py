from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import CurrentWeather, ForecastResponse, ErrorResponse
from app.weather_service import WeatherService
from app.cache import cache_info, clear_cache

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida: crea y cierra el cliente HTTP."""
    app.state.http_client = httpx.AsyncClient(timeout=15.0)
    app.state.weather_service = WeatherService(app.state.http_client)
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="🌦️ API de Clima",
    description=(
        "API REST para consultar el **clima actual** y **pronóstico a 5 días** "
        "de cualquier ciudad del mundo.\n\n"
        "Datos proporcionados por [OpenWeatherMap](https://openweathermap.org/).\n\n"
        "### Características\n"
        "- Búsqueda por nombre de ciudad o coordenadas (lat/lon)\n"
        "- Respuestas en español\n"
        "- Cache en memoria (10 min) para optimizar rendimiento\n"
        "- Temperaturas en grados Celsius (metric)\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    responses={
        404: {"model": ErrorResponse, "description": "Ciudad no encontrada"},
        401: {"model": ErrorResponse, "description": "API key inválida"},
        429: {"model": ErrorResponse, "description": "Límite de peticiones excedido"},
        503: {"model": ErrorResponse, "description": "Error de conexión"},
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
    """Verifica el estado del servicio y configuración del cache."""
    return {
        "status": "online",
        "service": "Weather API",
        "provider": "OpenWeatherMap",
        "cache": cache_info(),
        "documentation": "/docs",
    }


# ─── Clima Actual ────────────────────────────────────────────────────────────


@app.get(
    "/weather/coords",
    response_model=CurrentWeather,
    tags=["Clima Actual"],
    summary="Clima actual por coordenadas",
    description="Obtiene las condiciones climáticas actuales usando coordenadas geográficas (latitud y longitud).",
)
async def get_weather_by_coords(
    lat: float = Query(
        ...,
        description="Latitud",
        ge=-90,
        le=90,
        examples=[20.6597],
    ),
    lon: float = Query(
        ...,
        description="Longitud",
        ge=-180,
        le=180,
        examples=[-103.3496],
    ),
):
    service: WeatherService = app.state.weather_service
    return await service.get_current_weather_by_coords(lat, lon)


@app.get(
    "/weather/{city}",
    response_model=CurrentWeather,
    tags=["Clima Actual"],
    summary="Clima actual por ciudad",
    description="Obtiene las condiciones climáticas actuales de una ciudad por su nombre.",
)
async def get_weather_by_city(
    city: str = Path(
        ...,
        description="Nombre de la ciudad",
        examples=["Guadalajara", "Mexico City", "London"],
        min_length=1,
        max_length=100,
    ),
):
    service: WeatherService = app.state.weather_service
    return await service.get_current_weather(city)


# ─── Pronóstico 5 Días ──────────────────────────────────────────────────────


@app.get(
    "/forecast/coords",
    response_model=ForecastResponse,
    tags=["Pronóstico"],
    summary="Pronóstico a 5 días por coordenadas",
    description="Obtiene el pronóstico del clima cada 3 horas durante los próximos 5 días usando coordenadas.",
)
async def get_forecast_by_coords(
    lat: float = Query(
        ...,
        description="Latitud",
        ge=-90,
        le=90,
        examples=[20.6597],
    ),
    lon: float = Query(
        ...,
        description="Longitud",
        ge=-180,
        le=180,
        examples=[-103.3496],
    ),
):
    service: WeatherService = app.state.weather_service
    return await service.get_forecast_by_coords(lat, lon)


@app.get(
    "/forecast/{city}",
    response_model=ForecastResponse,
    tags=["Pronóstico"],
    summary="Pronóstico a 5 días por ciudad",
    description="Obtiene el pronóstico del clima cada 3 horas durante los próximos 5 días para una ciudad.",
)
async def get_forecast_by_city(
    city: str = Path(
        ...,
        description="Nombre de la ciudad",
        examples=["Guadalajara", "Mexico City", "London"],
        min_length=1,
        max_length=100,
    ),
):
    service: WeatherService = app.state.weather_service
    return await service.get_forecast(city)


# ─── Cache Management ───────────────────────────────────────────────────────


@app.get("/cache/status", tags=["Cache"], summary="Estado del cache")
async def get_cache_status():
    """Retorna el estado actual del cache en memoria."""
    return cache_info()


@app.delete("/cache", tags=["Cache"], summary="Limpiar cache")
async def delete_cache():
    """Limpia todas las entradas del cache."""
    clear_cache()
    return {"message": "Cache limpiado exitosamente", "cache": cache_info()}
