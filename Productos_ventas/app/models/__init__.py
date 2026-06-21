# Importar todos los modelos para que Alembic los detecte
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem

__all__ = ["User", "Category", "Product", "Inventory", "Order", "OrderItem"]
