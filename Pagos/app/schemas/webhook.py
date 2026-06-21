from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WebhookEventResponse(BaseModel):
    """Schema de respuesta de evento webhook (solo para consulta/auditoría)."""

    id: int
    gateway: str
    event_id: str
    event_type: str
    processed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
