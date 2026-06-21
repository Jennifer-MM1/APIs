from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Refund(Base):
    """Modelo de Reembolso — puede ser total o parcial, asociado a un pago."""

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)

    # Referencia externa en la pasarela
    gateway_refund_id = Column(String(255), nullable=True)

    # Monto (puede ser parcial)
    amount = Column(Numeric(12, 2), nullable=False)

    # Razón y estado
    reason = Column(String(30), default="requested_by_customer")
    status = Column(String(20), default="pending")  # pending, completed, failed
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    payment = relationship("Payment", back_populates="refunds")
