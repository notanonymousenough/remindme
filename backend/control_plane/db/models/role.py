from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Role(BaseModel):
    __tablename__ = 'roles'

    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)

    users = relationship("UserRole", back_populates="role")
    quotas = relationship("Quota", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name} ({self.id})>"


class UserRole(BaseModel):
    __tablename__ = 'user_roles'

    user_id = Column(UUID, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID, ForeignKey('roles.id', ondelete="CASCADE"), nullable=False)
    valid_from = Column(DateTime, default=func.now())
    valid_to = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<UserRole {self.user_id} - {self.role_id}>"