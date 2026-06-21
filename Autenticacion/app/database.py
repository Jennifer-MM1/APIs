import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

# Configuración de logs
logger = logging.getLogger("uvicorn.error")

settings = get_settings()

# Cliente de MongoDB
client = AsyncIOMotorClient(settings.MONGODB_URL)

# Base de datos activa
db = client[settings.DATABASE_NAME]


async def init_db():
    """Inicializa la base de datos creando los índices necesarios."""
    try:
        # Índice único para username
        username_index = await db.users.create_index("username", unique=True)
        # Índice único para email
        email_index = await db.users.create_index("email", unique=True)

        logger.info(f"Índices de base de datos inicializados correctamente: {username_index}, {email_index}")
    except Exception as e:
        logger.error(f"Error al inicializar los índices de la base de datos: {e}")
        raise e


async def close_db():
    """Cierra la conexión con el cliente de MongoDB."""
    client.close()
    logger.info("Conexión con MongoDB cerrada.")
