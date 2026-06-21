from typing import List
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import get_project_by_id, check_project_access
from app.utils.exceptions import NotFoundException, ForbiddenException, BadRequestException


def get_project_tasks(
    db: Session,
    project_id: int,
    user_id: int,
    status: str = None,
    priority: str = None,
) -> List[Task]:
    """Obtiene las tareas de un proyecto con filtros opcionales."""
    # Verificar acceso al proyecto (cualquier rol puede ver)
    get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id)

    query = db.query(Task).filter(Task.project_id == project_id)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    return query.order_by(Task.created_at.desc()).all()


def create_task(db: Session, project_id: int, data: TaskCreate, user_id: int) -> Task:
    """Crea una nueva tarea en un proyecto (admin o member)."""
    get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id, required_roles=["admin", "member"])

    # Validar prioridad
    valid_priorities = ["low", "medium", "high", "critical"]
    if data.priority not in valid_priorities:
        raise BadRequestException(
            detail=f"Prioridad inválida. Válidas: {', '.join(valid_priorities)}"
        )

    # Validar que el usuario asignado existe y es miembro del proyecto
    if data.assigned_to:
        assignee = db.query(User).filter(User.id == data.assigned_to).first()
        if not assignee:
            raise NotFoundException(detail=f"Usuario con ID {data.assigned_to} no encontrado")
        # Verificar que sea miembro del proyecto
        check_project_access(db, project_id, data.assigned_to)

    task = Task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        project_id=project_id,
        assigned_to=data.assigned_to,
        created_by=user_id,
        due_date=data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_by_id(db: Session, project_id: int, task_id: int, user_id: int) -> Task:
    """Obtiene una tarea por su ID."""
    get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id)

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id)
        .first()
    )
    if not task:
        raise NotFoundException(detail=f"Tarea con ID {task_id} no encontrada en este proyecto")
    return task


def update_task(db: Session, project_id: int, task_id: int, data: TaskUpdate, user_id: int) -> Task:
    """Actualiza una tarea (admin puede editar todas, member solo las asignadas a él)."""
    get_project_by_id(db, project_id)
    role = check_project_access(db, project_id, user_id, required_roles=["admin", "member"])

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id)
        .first()
    )
    if not task:
        raise NotFoundException(detail=f"Tarea con ID {task_id} no encontrada en este proyecto")

    # Los members solo pueden editar tareas asignadas a ellos
    if role == "member" and task.assigned_to != user_id:
        raise ForbiddenException(detail="Solo puedes editar tareas asignadas a ti")

    # Validar status si se proporciona
    if data.status:
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if data.status not in valid_statuses:
            raise BadRequestException(
                detail=f"Estado inválido. Válidos: {', '.join(valid_statuses)}"
            )

    # Validar prioridad si se proporciona
    if data.priority:
        valid_priorities = ["low", "medium", "high", "critical"]
        if data.priority not in valid_priorities:
            raise BadRequestException(
                detail=f"Prioridad inválida. Válidas: {', '.join(valid_priorities)}"
            )

    # Validar assigned_to si se proporciona
    if data.assigned_to is not None:
        assignee = db.query(User).filter(User.id == data.assigned_to).first()
        if not assignee:
            raise NotFoundException(detail=f"Usuario con ID {data.assigned_to} no encontrado")
        check_project_access(db, project_id, data.assigned_to)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, project_id: int, task_id: int, user_id: int) -> None:
    """Elimina una tarea (solo admin)."""
    get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id, required_roles=["admin"])

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id)
        .first()
    )
    if not task:
        raise NotFoundException(detail=f"Tarea con ID {task_id} no encontrada en este proyecto")

    db.delete(task)
    db.commit()
