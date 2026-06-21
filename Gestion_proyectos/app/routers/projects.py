from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectMemberResponse,
    AddMemberRequest,
)
from app.services import project_service
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar proyectos del usuario autenticado (como dueño o miembro)."""
    return project_service.get_user_projects(db, current_user.id)


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear un nuevo proyecto. El creador se asigna automáticamente como admin."""
    return project_service.create_project(db, data, current_user.id)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener un proyecto con sus miembros (requiere ser miembro)."""
    project_service.check_project_access(db, project_id, current_user.id)
    project = project_service.get_project_by_id(db, project_id)

    # Construir respuesta con miembros
    members = []
    for m in project.members:
        members.append(
            ProjectMemberResponse(
                id=m.id,
                user_id=m.user_id,
                username=m.user.username,
                role=m.role,
                joined_at=m.joined_at,
            )
        )

    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        owner_id=project.owner_id,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
        updated_at=project.updated_at,
        members=members,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar un proyecto (solo admin)."""
    return project_service.update_project(db, project_id, data, current_user.id)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar un proyecto (solo el dueño/owner)."""
    project_service.delete_project(db, project_id, current_user.id)


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=201)
def add_member(
    project_id: int,
    data: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agregar un miembro al proyecto (solo admin)."""
    member = project_service.add_member(db, project_id, data, current_user.id)
    return ProjectMemberResponse(
        id=member.id,
        user_id=member.user_id,
        username=member.user.username,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remover un miembro del proyecto (solo admin, no puede remover al dueño)."""
    project_service.remove_member(db, project_id, user_id, current_user.id)
