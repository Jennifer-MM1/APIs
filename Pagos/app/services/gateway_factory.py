from app.config import get_settings
from app.services.gateway_base import PaymentGateway
from app.services.stripe_gateway import StripeGateway
from app.services.paypal_gateway import PayPalGateway
from app.services.mercadopago_gateway import MercadoPagoGateway
from app.utils.exceptions import InvalidGatewayException

settings = get_settings()

# Mapeo de nombre → clase de gateway
_GATEWAY_MAP: dict[str, type[PaymentGateway]] = {
    "stripe": StripeGateway,
    "paypal": PayPalGateway,
    "mercadopago": MercadoPagoGateway,
}


def get_gateway(gateway_name: str) -> PaymentGateway:
    """Factory que instancia el gateway correcto según el nombre.

    Verifica que el gateway exista y que tenga las API keys configuradas.

    Args:
        gateway_name: Nombre del gateway ("stripe", "paypal", "mercadopago").

    Returns:
        Instancia del gateway solicitado.

    Raises:
        InvalidGatewayException: Si el gateway no existe o no tiene API keys.
    """
    available = settings.get_available_gateways()

    if gateway_name not in _GATEWAY_MAP:
        raise InvalidGatewayException(gateway_name, available)

    if gateway_name not in available:
        raise InvalidGatewayException(gateway_name, available)

    gateway_class = _GATEWAY_MAP[gateway_name]
    return gateway_class(settings)
