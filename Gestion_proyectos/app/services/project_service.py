from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, AddMemberRequest
from app.utils.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    ConflictException,
)


def get_user_projects(db: Session, user_id: int) -> List[Project]:
    """Obtiene todos los proyectos donde el usuario es miembro o dueño."""
    # Proyectos donde es dueño
    owned = db.query(Project).filter(Project.owner_id == user_id).all()

    # Proyectos donde es miembro (pero no dueño)
    member_project_ids = (
        db.query(ProjectMember.project_id)
        .filter(ProjectMember.user_id == user_id)
        .all()
    )
    member_ids = [pid[0] for pid in member_project_ids]

    member_projects = (
        db.query(Project)
        .filter(Project.id.in_(member_ids), Project.owner_id != user_id)
        .all()
    )

    return owned + member_projects


def create_project(db: Session, data: ProjectCreate, owner_id: int) -> Project:
    """Crea un nuevo proyecto y agrega al dueño como admin."""
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(project)
    db.flush()  # Para obtener el ID del proyecto

    # Agregar al dueño como miembro admin
    member = ProjectMember(
        user_id=owner_id,
        project_id=project.id,
        role="admin",
    )
    db.add(member)
    db.commit()
    db.refresh(project)
    return project


def get_project_by_id(db: Session, project_id: int) -> Project:
    """Obtiene un proyecto por su ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundException(detail=f"Proyecto con ID {project_id} no encontrado")
    return project


def get_member_role(db: Session, project_id: int, user_id: int) -> Optional[str]:
    """Obtiene el rol de un usuario en un proyecto. Retorna None si no es miembro."""
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    return member.role if member else None


def check_project_access(db: Session, project_id: int, user_id: int, required_roles: List[str] = None) -> str:
    """
    Verifica que el usuario tenga acceso al proyecto.
    Si se especifican roles requeridos, verifica que el usuario tenga uno de ellos.
    Retorna el rol del usuario.
    """
    role = get_member_role(db, project_id, user_id)
    if role is None:
        raise ForbiddenException(detail="No eres miembro de este proyecto")

    if required_roles and role not in required_roles:
        raise ForbiddenException(
            detail=f"Se requiere rol {' o '.join(required_roles)}. Tu rol es: {role}"
        )

    return role


def update_project(db: Session, project_id: int, data: ProjectUpdate, user_id: int) -> Project:
    """Actualiza un proyecto (solo admin)."""
    project = get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id, required_roles=["admin"])

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    """Elimina un proyecto (solo el dueño/owner)."""
    project = get_project_by_id(db, project_id)

    if project.owner_id != user_id:
        raise ForbiddenException(detail="Solo el dueño del proyecto puede eliminarlo")

    db.delete(project)
    db.commit()


def add_member(db: Session, project_id: int, data: AddMemberRequest, user_id: int) -> ProjectMember:
    """Agrega un miembro al proyecto (solo admin)."""
    get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id, required_roles=["admin"])

    # Validar rol
    valid_roles = ["admin", "member", "viewer"]
    if data.role not in valid_roles:
        raise BadRequestException(
            detail=f"Rol inválido. Roles válidos: {', '.join(valid_roles)}"
        )

    # Verificar que el usuario a agregar existe
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise NotFoundException(detail=f"Usuario con ID {data.user_id} no encontrado")

    # Verificar que no sea ya miembro
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
        )
        .first()
    )
    if existing:
        raise ConflictException(detail="El usuario ya es miembro de este proyecto")

    member = ProjectMember(
        user_id=data.user_id,
        project_id=project_id,
        role=data.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, project_id: int, target_user_id: int, user_id: int) -> None:
    """Remueve un miembro del proyecto (solo admin, no puede remover al dueño)."""
    project = get_project_by_id(db, project_id)
    check_project_access(db, project_id, user_id, required_roles=["admin"])

    # No se puede remover al dueño
    if target_user_id == project.owner_id:
        raise BadRequestException(detail="No se puede remover al dueño del proyecto")

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id,
        )
        .first()
    )
    if not member:
        raise NotFoundException(detail="El usuario no es miembro de este proyecto")

    db.delete(member)
    db.commit()
