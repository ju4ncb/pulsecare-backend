from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_role: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, default=1)  # 1: Estudiante, 2: Admin
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # john@doe.com
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False) # hashed con PBKDF2
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # para soft delete o desactivación de cuenta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False) # timestamp de creación
    
    wellbeing_entries = relationship("WellbeingEntry", back_populates="user", cascade="all, delete-orphan", passive_deletes=True) # relación uno a muchos con registros de bienestar
    role = relationship("Role", back_populates="users") # relación con Role, permite acceder a los datos del rol desde el usuario

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # nombre del rol, e.g. "Estudiante", "Admin"

    users = relationship("User", back_populates="role") # relación con User, permite acceder a los usuarios que tienen este rol