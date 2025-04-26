from sqlalchemy import Column, String, Text, ForeignKey, Enum, DateTime, func, Integer, UniqueConstraint, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class ResourceType(BaseModel):
    __tablename__ = 'resource_types'

    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    quotas = relationship("Quota", back_populates="resource_type")
    quota_usages = relationship("QuotaUsage", back_populates="resource_type")

    def __repr__(self):
        return f"<ResourceType {self.name}>"


class Quota(BaseModel):
    __tablename__ = 'quotas'

    role_id = Column(UUID, ForeignKey('roles.id', ondelete="CASCADE"), nullable=False)
    resource_type_id = Column(UUID, ForeignKey('resource_types.id', ondelete="CASCADE"), nullable=False)
    max_value = Column(Numeric(10, 4), nullable=False)

    role = relationship("Role", back_populates="quotas")
    resource_type = relationship("ResourceType", back_populates="quotas")

    __table_args__ = (
        UniqueConstraint('role_id', 'resource_type_id', name='unique_role_resource'),
    )

    def __repr__(self):
        return f"<Quota {self.resource_type.name} - {self.max_value}>"


class QuotaUsage(BaseModel):
    __tablename__ = 'quota_usages'

    user_id = Column(UUID, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    resource_type_id = Column(UUID, ForeignKey('resource_types.id', ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    usage_value = Column(Numeric(10, 4), nullable=False, default=0)

    user = relationship("User", back_populates="quota_usages")
    resource_type = relationship("ResourceType", back_populates="quota_usages")

    __table_args__ = (
        UniqueConstraint('user_id', 'resource_type_id', 'date', name='unique_user_resource_date'),
    )

    def __repr__(self):
        return f"<QuotaUsage {self.resource_type.name} - {self.usage_value}>"
