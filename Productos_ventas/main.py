from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, categories, products, inventory, orders

app = FastAPI(
    title="API Productos y Ventas — Tienda de Tecnología",
    description=(
        "API REST para gestión de productos, categorías, inventario y pedidos "
        "de una tienda de tecnología (laptops, celulares y accesorios). "
        "Incluye autenticación JWT, roles (admin/customer), operaciones de venta "
        "con control de stock e IVA 16%."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - Permite conexiones desde apps web y móviles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categorías"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Productos"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventario"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Pedidos"])


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "API de Productos y Ventas — Tienda de Tecnología",
        "version": "1.0.0",
        "docs": "/docs",
    }
