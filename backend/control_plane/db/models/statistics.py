from sqlalchemy import Column, Integer, Date, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserStatistics(BaseModel):
    __tablename__ = "user_statistics"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    reminders_completed = Column(Integer, default=0)
    reminders_forgotten = Column(Integer, default=0)
    last_calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Отношения
    user = relationship("User", back_populates="statistics")

    def __repr__(self):
        return f"<UserStatistics user={self.user_id}>"
