from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import customers, plans, payments, subscriptions, refunds, webhooks
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="API de Pagos — Multi-Gateway",
    description=(
        "API REST para gestión de pagos, suscripciones, reembolsos y webhooks. "
        "Soporta múltiples pasarelas: Stripe, PayPal y MercadoPago. "
        "Base de datos: Turso (libSQL). Autenticación: JWT compartido."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — Permite conexiones desde apps web y móviles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Clientes"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["Planes"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Pagos"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Suscripciones"])
app.include_router(refunds.router, prefix="/api/v1/refunds", tags=["Reembolsos"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])


@app.get("/", tags=["Root"])
def root():
    """Ruta raíz — muestra estado del servicio y gateways disponibles."""
    available_gateways = settings.get_available_gateways()
    return {
        "status": "online",
        "service": "API de Pagos — Multi-Gateway",
        "version": "1.0.0",
        "database": "Turso (libSQL)",
        "default_currency": settings.DEFAULT_CURRENCY,
        "gateways_configured": available_gateways,
        "gateways_total": len(available_gateways),
        "docs": "/docs",
    }
