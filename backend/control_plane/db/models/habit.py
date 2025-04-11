from sqlalchemy import Column, Text, Date, Boolean, ForeignKey, Enum, Integer, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel, HabitPeriod


class Habit(BaseModel):
    __tablename__ = "habits"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    interval = Column(Enum(HabitPeriod), nullable=False)
    custom_interval = Column(Text)
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    removed = Column(Boolean, default=False)

    # Отношения
    user = relationship("User", back_populates="habits")
    progress_records = relationship("HabitProgress", back_populates="habit", cascade="all, delete-orphan")
    neuro_images = relationship("NeuroImage", back_populates="habit")

    def __repr__(self):
        return f"<Habit {self.text[:20]}... ({self.id})>"


class HabitProgress(BaseModel):
    __tablename__ = "habit_progress"

    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)

    # Отношения
    habit = relationship("Habit", back_populates="progress_records")

    # Ограничения
    __table_args__ = (
        UniqueConstraint('habit_id', 'date', name='uq_habit_date'),
    )

    def __repr__(self):
        return f"<HabitProgress habit={self.habit_id} date={self.date}>"
