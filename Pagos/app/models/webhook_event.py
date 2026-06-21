from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from app.database import Base


class WebhookEvent(Base):
    """Modelo de Evento Webhook — log inmutable para idempotencia y auditoría."""

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    gateway = Column(String(20), nullable=False)  # stripe, paypal, mercadopago
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # payment.completed, subscription.cancelled, etc.
    payload = Column(Text, nullable=False)  # JSON string completo del evento
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
