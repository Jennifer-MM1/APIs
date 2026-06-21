from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Plan(Base):
    """Modelo de Plan de Suscripción — define planes recurrentes con sus IDs por pasarela."""

    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="MXN")
    interval = Column(String(10), nullable=False)  # week, month, year
    interval_count = Column(Integer, default=1)  # Ej: 3 = cada 3 meses

    # IDs externos en cada pasarela (se crean al sincronizar el plan)
    stripe_price_id = Column(String(255), nullable=True)
    paypal_plan_id = Column(String(255), nullable=True)
    mercadopago_plan_id = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    subscriptions = relationship("Subscription", back_populates="plan")
