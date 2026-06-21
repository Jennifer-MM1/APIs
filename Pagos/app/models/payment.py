from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
    """Modelo de Pago — transacción principal vinculada a un cliente y gateway."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Gateway y referencia externa
    gateway = Column(String(20), nullable=False)  # stripe, paypal, mercadopago
    gateway_payment_id = Column(String(255), nullable=True)  # ID del pago en la pasarela

    # Monto y moneda
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="MXN")

    # Estado del pago
    status = Column(String(20), default="pending")  # pending, processing, completed, failed, cancelled

    # Información adicional
    description = Column(String(500), nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON string con datos extra
    gateway_response = Column(Text, nullable=True)  # Respuesta raw de la pasarela
    checkout_url = Column(String(1000), nullable=True)  # URL de checkout (PayPal/MP)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    customer = relationship("Customer", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment")
