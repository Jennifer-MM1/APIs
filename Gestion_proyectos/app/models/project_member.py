from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class ProjectMember(Base):
    """Modelo de Miembro de Proyecto (tabla intermedia con rol)."""

    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role = Column(String(20), default="member")  # admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Restricción: un usuario solo puede ser miembro una vez por proyecto
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_user_project"),
    )

    # Relaciones
    user = relationship("User", back_populates="project_memberships")
    project = relationship("Project", back_populates="members")
