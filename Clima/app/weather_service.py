import httpx
from fastapi import HTTPException

from app.config import get_settings
from app.schemas import CurrentWeather, ForecastItem, ForecastResponse, Coordinates
from app.cache import get_cache_key, get_cached, set_cached

settings = get_settings()

ICON_URL_TEMPLATE = "https://openweathermap.org/img/wn/{icon}@2x.png"


class WeatherService:
    """Servicio para consultar datos del clima desde OpenWeatherMap."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.api_key = settings.OPENWEATHER_API_KEY
        self.lang = settings.DEFAULT_LANG
        self.units = settings.DEFAULT_UNITS

    def _base_params(self) -> dict:
        """Parámetros base para todas las peticiones a OpenWeatherMap."""
        return {
            "appid": self.api_key,
            "lang": self.lang,
            "units": self.units,
        }

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Realiza una petición HTTP a OpenWeatherMap y maneja errores."""
        url = f"{self.base_url}/{endpoint}"
        all_params = {**self._base_params(), **params}

        try:
            response = await self.client.get(url, params=all_params)
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error de conexión con OpenWeatherMap: {str(e)}",
            )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="API key de OpenWeatherMap inválida o no configurada. "
                       "Verifica tu OPENWEATHER_API_KEY en el archivo .env",
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Ciudad no encontrada. Verifica el nombre e intenta de nuevo.",
            )
        elif response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Límite de peticiones a OpenWeatherMap excedido. Intenta más tarde.",
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Error inesperado de OpenWeatherMap (HTTP {response.status_code}).",
            )

        return response.json()

    def _parse_current_weather(self, data: dict) -> CurrentWeather:
        """Transforma la respuesta cruda de OpenWeatherMap a nuestro schema."""
        weather_info = data["weather"][0]
        main = data["main"]
        wind = data.get("wind", {})
        icon_code = weather_info["icon"]

        return CurrentWeather(
            city=data["name"],
            country=data["sys"]["country"],
            temperature=main["temp"],
            feels_like=main["feels_like"],
            temp_min=main["temp_min"],
            temp_max=main["temp_max"],
            humidity=main["humidity"],
            description=weather_info["description"],
            icon=icon_code,
            icon_url=ICON_URL_TEMPLATE.format(icon=icon_code),
            wind_speed=wind.get("speed", 0),
            wind_deg=wind.get("deg"),
            pressure=main["pressure"],
            visibility=data.get("visibility"),
            clouds=data.get("clouds", {}).get("all", 0),
            coordinates=Coordinates(
                lat=data["coord"]["lat"],
                lon=data["coord"]["lon"],
            ),
        )

    def _parse_forecast(self, data: dict) -> ForecastResponse:
        """Transforma la respuesta del pronóstico al schema de respuesta."""
        city_info = data["city"]
        items = []

        for item in data["list"]:
            weather_info = item["weather"][0]
            icon_code = weather_info["icon"]

            items.append(
                ForecastItem(
                    datetime=item["dt_txt"],
                    temperature=item["main"]["temp"],
                    feels_like=item["main"]["feels_like"],
                    temp_min=item["main"]["temp_min"],
                    temp_max=item["main"]["temp_max"],
                    humidity=item["main"]["humidity"],
                    description=weather_info["description"],
                    icon=icon_code,
                    icon_url=ICON_URL_TEMPLATE.format(icon=icon_code),
                    wind_speed=item.get("wind", {}).get("speed", 0),
                    clouds=item.get("clouds", {}).get("all", 0),
                    rain_probability=item.get("pop", 0),
                )
            )

        return ForecastResponse(
            city=city_info["name"],
            country=city_info["country"],
            coordinates=Coordinates(
                lat=city_info["coord"]["lat"],
                lon=city_info["coord"]["lon"],
            ),
            total_items=len(items),
            forecast=items,
        )

    # --- Métodos públicos ---

    async def get_current_weather(self, city: str) -> CurrentWeather:
        """Obtiene el clima actual de una ciudad por nombre."""
        cache_key = get_cache_key("weather", city=city.lower())
        cached = get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("weather", {"q": city})
        result = self._parse_current_weather(data)
        set_cached(cache_key, result)
        return result

    async def get_current_weather_by_coords(self, lat: float, lon: float) -> CurrentWeather:
        """Obtiene el clima actual por coordenadas geográficas."""
        cache_key = get_cache_key("weather", lat=round(lat, 4), lon=round(lon, 4))
        cached = get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("weather", {"lat": lat, "lon": lon})
        result = self._parse_current_weather(data)
        set_cached(cache_key, result)
        return result

    async def get_forecast(self, city: str) -> ForecastResponse:
        """Obtiene el pronóstico a 5 días de una ciudad por nombre."""
        cache_key = get_cache_key("forecast", city=city.lower())
        cached = get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("forecast", {"q": city})
        result = self._parse_forecast(data)
        set_cached(cache_key, result)
        return result

    async def get_forecast_by_coords(self, lat: float, lon: float) -> ForecastResponse:
        """Obtiene el pronóstico a 5 días por coordenadas geográficas."""
        cache_key = get_cache_key("forecast", lat=round(lat, 4), lon=round(lon, 4))
        cached = get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("forecast", {"lat": lat, "lon": lon})
        result = self._parse_forecast(data)
        set_cached(cache_key, result)
        return result
