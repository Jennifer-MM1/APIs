from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación. Lee variables del archivo .env"""

    # --- Base de datos ---
    # Para desarrollo local (SQLite): sqlite:///pagos.db
    # Para Turso (producción):        sqlite+libsql://tu-db.turso.io?secure=true
    DATABASE_URL: str = "sqlite:///pagos.db"
    TURSO_AUTH_TOKEN: Optional[str] = None

    # --- JWT (compartido con API de Autenticación) ---
    SECRET_KEY: str = "default-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    # --- Moneda por defecto ---
    DEFAULT_CURRENCY: str = "MXN"

    # --- Stripe (opcional) ---
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # --- PayPal (opcional) ---
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_MODE: str = "sandbox"  # "sandbox" o "live"

    # --- MercadoPago (opcional) ---
    MERCADOPAGO_ACCESS_TOKEN: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def paypal_base_url(self) -> str:
        """URL base de PayPal según el modo (sandbox/live)."""
        if self.PAYPAL_MODE == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    def get_available_gateways(self) -> list[str]:
        """Retorna la lista de gateways configurados (con API keys presentes)."""
        available = []
        if self.STRIPE_SECRET_KEY:
            available.append("stripe")
        if self.PAYPAL_CLIENT_ID and self.PAYPAL_CLIENT_SECRET:
            available.append("paypal")
        if self.MERCADOPAGO_ACCESS_TOKEN:
            available.append("mercadopago")
        return available


@lru_cache()
def get_settings() -> Settings:
    """Retorna la configuración cacheada (singleton)."""
    return Settings()
