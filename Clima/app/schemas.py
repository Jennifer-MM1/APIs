from pydantic import BaseModel, Field
from typing import Optional


class Coordinates(BaseModel):
    """Coordenadas geográficas de la ubicación."""

    lat: float = Field(..., description="Latitud", examples=[20.6597])
    lon: float = Field(..., description="Longitud", examples=[-103.3496])


class CurrentWeather(BaseModel):
    """Respuesta del clima actual de una ciudad."""

    city: str = Field(..., description="Nombre de la ciudad", examples=["Guadalajara"])
    country: str = Field(..., description="Código de país", examples=["MX"])
    temperature: float = Field(..., description="Temperatura actual (°C)", examples=[28.5])
    feels_like: float = Field(..., description="Sensación térmica (°C)", examples=[30.1])
    temp_min: float = Field(..., description="Temperatura mínima (°C)", examples=[25.0])
    temp_max: float = Field(..., description="Temperatura máxima (°C)", examples=[31.0])
    humidity: int = Field(..., description="Humedad relativa (%)", examples=[65])
    description: str = Field(..., description="Descripción del clima", examples=["nubes dispersas"])
    icon: str = Field(..., description="Código del ícono del clima", examples=["03d"])
    wind_speed: float = Field(..., description="Velocidad del viento (m/s)", examples=[3.2])
    wind_deg: Optional[int] = Field(None, description="Dirección del viento (grados)", examples=[180])
    pressure: int = Field(..., description="Presión atmosférica (hPa)", examples=[1013])
    visibility: Optional[int] = Field(None, description="Visibilidad (metros)", examples=[10000])
    clouds: int = Field(..., description="Nubosidad (%)", examples=[40])
    coordinates: Coordinates = Field(..., description="Coordenadas de la ciudad")
    icon_url: str = Field(..., description="URL del ícono del clima", examples=["https://openweathermap.org/img/wn/03d@2x.png"])


class ForecastItem(BaseModel):
    """Un punto de datos del pronóstico (cada 3 horas)."""

    datetime: str = Field(..., description="Fecha y hora del pronóstico", examples=["2026-06-22 12:00:00"])
    temperature: float = Field(..., description="Temperatura (°C)", examples=[30.2])
    feels_like: float = Field(..., description="Sensación térmica (°C)", examples=[32.0])
    temp_min: float = Field(..., description="Temperatura mínima (°C)", examples=[28.0])
    temp_max: float = Field(..., description="Temperatura máxima (°C)", examples=[32.5])
    humidity: int = Field(..., description="Humedad relativa (%)", examples=[55])
    description: str = Field(..., description="Descripción del clima", examples=["cielo claro"])
    icon: str = Field(..., description="Código del ícono", examples=["01d"])
    icon_url: str = Field(..., description="URL del ícono del clima", examples=["https://openweathermap.org/img/wn/01d@2x.png"])
    wind_speed: float = Field(..., description="Velocidad del viento (m/s)", examples=[2.8])
    clouds: int = Field(..., description="Nubosidad (%)", examples=[10])
    rain_probability: float = Field(..., description="Probabilidad de lluvia (0-1)", examples=[0.1])


class ForecastResponse(BaseModel):
    """Respuesta del pronóstico a 5 días de una ciudad."""

    city: str = Field(..., description="Nombre de la ciudad", examples=["Guadalajara"])
    country: str = Field(..., description="Código de país", examples=["MX"])
    coordinates: Coordinates = Field(..., description="Coordenadas de la ciudad")
    total_items: int = Field(..., description="Número total de puntos en el pronóstico", examples=[40])
    forecast: list[ForecastItem] = Field(..., description="Lista de pronósticos cada 3 horas")


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada."""

    detail: str = Field(..., description="Mensaje de error descriptivo")
    status_code: int = Field(..., description="Código HTTP del error")
