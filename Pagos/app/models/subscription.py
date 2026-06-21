from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Subscription(Base):
    """Modelo de Suscripción — vincula un cliente a un plan recurrente vía un gateway."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    # Gateway y referencia externa
    gateway = Column(String(20), nullable=False)  # stripe, paypal, mercadopago
    gateway_subscription_id = Column(String(255), nullable=True)

    # Estado y período actual
    status = Column(String(20), default="active")  # active, paused, cancelled, past_due, expired
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # URL de aprobación (para PayPal/MP donde el usuario debe aprobar)
    approval_url = Column(String(1000), nullable=True)

    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
