from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ProjectCreate(BaseModel):
    """Schema para crear un proyecto."""

    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    """Schema para actualizar un proyecto."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # active, completed, archived
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectMemberResponse(BaseModel):
    """Schema de respuesta de miembro de proyecto."""

    id: int
    user_id: int
    username: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    """Schema de respuesta de proyecto."""

    id: int
    name: str
    description: Optional[str] = None
    status: str
    owner_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    """Schema de respuesta de proyecto con miembros."""

    members: List[ProjectMemberResponse] = []


class AddMemberRequest(BaseModel):
    """Schema para agregar un miembro al proyecto."""

    user_id: int
    role: str = "member"  # admin, member, viewer
