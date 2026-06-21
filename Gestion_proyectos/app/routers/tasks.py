from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services import task_service
from app.models.user import User

router = APIRouter()


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
def list_tasks(
    project_id: int,
    status: Optional[str] = Query(None, description="Filtrar por estado: pending, in_progress, completed, cancelled"),
    priority: Optional[str] = Query(None, description="Filtrar por prioridad: low, medium, high, critical"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar tareas de un proyecto con filtros opcionales."""
    return task_service.get_project_tasks(
        db, project_id, current_user.id, status=status, priority=priority
    )


@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear una tarea en un proyecto (admin o member)."""
    return task_service.create_task(db, project_id, data, current_user.id)


@router.get("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener una tarea por su ID."""
    return task_service.get_task_by_id(db, project_id, task_id, current_user.id)


@router.put("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar una tarea (admin puede editar todas, member solo las suyas)."""
    return task_service.update_task(db, project_id, task_id, data, current_user.id)


@router.delete("/{project_id}/tasks/{task_id}", status_code=204)
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar una tarea (solo admin)."""
    task_service.delete_task(db, project_id, task_id, current_user.id)
