"""Script para inicializar las tablas en Turso (libSQL).

Uso:
    python init_db.py

Esto crea todas las tablas definidas en app/models/ en la base de datos
configurada en .env (TURSO_DATABASE_URL + TURSO_AUTH_TOKEN).

Nota: libSQL no soporta Alembic nativamente, por lo que usamos
Base.metadata.create_all() para crear las tablas directamente.
"""

from app.database import engine, Base

# Importar todos los modelos para que SQLAlchemy los registre
from app.models import Customer, Plan, Payment, Subscription, Refund, WebhookEvent  # noqa


def init_database():
    """Crea todas las tablas en la base de datos."""
    print("=" * 50)
    print("  Inicializando base de datos")
    print("=" * 50)

    print("\nCreando tablas...")
    Base.metadata.create_all(bind=engine)

    # Listar tablas creadas
    table_names = list(Base.metadata.tables.keys())
    for table in table_names:
        print(f"  [OK] {table}")

    print(f"\n{len(table_names)} tablas creadas exitosamente.")
    print("=" * 50)


if __name__ == "__main__":
    init_database()
