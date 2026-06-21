from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    """Modelo de Cliente — registra clientes con sus IDs externos por pasarela."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)

    # IDs externos en cada pasarela (se crean al registrar el cliente ahí)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    paypal_customer_id = Column(String(255), nullable=True)
    mercadopago_customer_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    payments = relationship("Payment", back_populates="customer")
    subscriptions = relationship("Subscription", back_populates="customer")
