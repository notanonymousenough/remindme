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
    # user = relationship("User", back_populates="statistics")
    # daily_activities = relationship("DailyActivity", back_populates="statistics", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserStatistics user={self.user_id}>"


"""class DailyActivity(BaseModel):
    __tablename__ = "daily_activity"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user_statistics.user_id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    completed_items = Column(Integer, default=0)

    # Отношения
    # statistics = relationship("UserStatistics", back_populates="daily_activities")

    # Ограничения
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

    def __repr__(self):
        return f"<DailyActivity user={self.user_id} date={self.date}>"
"""