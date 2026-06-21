from typing import List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.order import OrderCreate, OrderBriefResponse
from app.config import get_settings
from app.utils.exceptions import (
    NotFoundException,
    InsufficientStockException,
    InvalidOperationException,
)

settings = get_settings()

# Transiciones de estado válidas
VALID_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["shipped", "cancelled"],
    "shipped": ["delivered"],
    "delivered": [],
    "cancelled": [],
}


def _generate_order_number(db: Session) -> str:
    """Genera un número de orden único con formato ORD-YYYYMMDD-NNNN."""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"ORD-{today}-"

    # Buscar la última orden del día
    last_order = (
        db.query(Order)
        .filter(Order.order_number.like(f"{prefix}%"))
        .order_by(Order.id.desc())
        .first()
    )

    if last_order:
        last_num = int(last_order.order_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}{new_num:04d}"


def create_order(db: Session, data: OrderCreate, user: User) -> Order:
    """
    Crea un pedido completo — operación de venta.

    1. Valida que todos los productos existen y están activos
    2. Verifica stock disponible para cada item
    3. Calcula subtotal, tax (16% IVA), total
    4. Descuenta stock del inventario
    5. Genera número de orden único
    6. Crea orden + items en una transacción
    """
    if not data.items:
        raise InvalidOperationException(detail="El pedido debe tener al menos un producto")

    order_subtotal = Decimal("0.00")
    order_items = []

    for item_data in data.items:
        # 1. Validar producto
        product = (
            db.query(Product)
            .options(joinedload(Product.inventory))
            .filter(Product.id == item_data.product_id)
            .first()
        )

        if not product:
            raise NotFoundException(
                detail=f"Producto con ID {item_data.product_id} no encontrado"
            )

        if not product.is_active:
            raise InvalidOperationException(
                detail=f"El producto '{product.name}' no está disponible"
            )

        # 2. Verificar stock
        if not product.inventory or product.inventory.stock < item_data.quantity:
            available = product.inventory.stock if product.inventory else 0
            raise InsufficientStockException(
                product_name=product.name,
                available=available,
                requested=item_data.quantity,
            )

        # 3. Calcular subtotal del item
        item_subtotal = product.price * item_data.quantity

        order_items.append({
            "product": product,
            "quantity": item_data.quantity,
            "unit_price": product.price,
            "subtotal": item_subtotal,
        })

        order_subtotal += item_subtotal

    # 4. Calcular totales
    tax = (order_subtotal * Decimal(str(settings.TAX_RATE))).quantize(Decimal("0.01"))
    total = order_subtotal + tax

    # 5. Generar número de orden
    order_number = _generate_order_number(db)

    # 6. Crear la orden
    order = Order(
        order_number=order_number,
        user_id=user.id,
        status="pending",
        subtotal=order_subtotal,
        tax=tax,
        total=total,
        shipping_address=data.shipping_address,
        notes=data.notes,
    )
    db.add(order)
    db.flush()

    # 7. Crear los items y descontar stock
    for item_info in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_info["product"].id,
            quantity=item_info["quantity"],
            unit_price=item_info["unit_price"],
            subtotal=item_info["subtotal"],
        )
        db.add(order_item)

        # Descontar stock
        item_info["product"].inventory.stock -= item_info["quantity"]

    db.commit()

    # Retornar orden completa con relaciones
    return get_order_by_id(db, order.id, user)


def get_order_by_id(db: Session, order_id: int, user: User) -> Order:
    """Obtiene un pedido por su ID. Los clientes solo ven sus propios pedidos."""
    query = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
    )

    # Los clientes solo pueden ver sus propios pedidos
    if user.role != "admin":
        query = query.filter(Order.user_id == user.id)

    order = query.first()
    if not order:
        raise NotFoundException(detail=f"Pedido con ID {order_id} no encontrado")
    return order


def get_user_orders(
    db: Session,
    user: User,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> List[OrderBriefResponse]:
    """Obtiene los pedidos del usuario (o todos si es admin)."""
    query = db.query(Order).options(joinedload(Order.items))

    # Los clientes solo ven sus pedidos
    if user.role != "admin":
        query = query.filter(Order.user_id == user.id)

    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return [
        OrderBriefResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total=order.total,
            created_at=order.created_at,
            items_count=len(order.items),
        )
        for order in orders
    ]


def update_order_status(db: Session, order_id: int, new_status: str, user: User) -> Order:
    """Actualiza el estado de un pedido siguiendo las transiciones válidas."""
    order = get_order_by_id(db, order_id, user)

    # Validar transición de estado
    valid_next = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in valid_next:
        raise InvalidOperationException(
            detail=f"No se puede cambiar el estado de '{order.status}' a '{new_status}'. "
            f"Transiciones válidas: {valid_next}"
        )

    order.status = new_status
    db.commit()
    db.refresh(order)

    return get_order_by_id(db, order.id, user)


def cancel_order(db: Session, order_id: int, user: User) -> Order:
    """
    Cancela un pedido y restaura el stock al inventario.
    Solo se pueden cancelar pedidos en estado 'pending' o 'confirmed'.
    """
    order = get_order_by_id(db, order_id, user)

    if order.status not in ("pending", "confirmed"):
        raise InvalidOperationException(
            detail=f"No se puede cancelar un pedido en estado '{order.status}'. "
            f"Solo se pueden cancelar pedidos pendientes o confirmados."
        )

    # Restaurar stock
    for item in order.items:
        inventory = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
        if inventory:
            inventory.stock += item.quantity

    order.status = "cancelled"
    db.commit()

    return get_order_by_id(db, order.id, user)
