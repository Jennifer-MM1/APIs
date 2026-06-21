from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    """Schema para crear una tarea."""

    title: str
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Schema para actualizar una tarea."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed, cancelled
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Schema de respuesta de tarea."""

    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    project_id: int
    assigned_to: Optional[int] = None
    created_by: int
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
