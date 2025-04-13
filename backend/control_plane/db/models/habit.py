from calendar import month
from datetime import datetime, timedelta

from sqlalchemy import Column, Text, Date, Boolean, ForeignKey, Enum, Integer, UniqueConstraint, DateTime, event, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from .base import BaseModel, HabitPeriod


class Habit(BaseModel):
    __tablename__ = "habits"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    interval = Column(Enum(HabitPeriod), nullable=False)  # можно выполнить раз в *interval*
    custom_interval = Column(Text, nullable=True)  # после MVP можно поменять на Integer - количество дней/недель и тд
    # progress column is removed - now derived from HabitProgress
    best_streak = Column(Integer, default=0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    removed = Column(Boolean, default=False)

    # Backing column for current_streak
    _current_streak = Column("current_streak", Integer, default=0)

    # Отношения
    user = relationship("User", back_populates="habits")
    progress_records = relationship("HabitProgress", back_populates="habit", cascade="all, delete-orphan")  # lazy='selectin' для оптимизации загрузки
    neuro_images = relationship("NeuroImage", back_populates="habit")

    def __repr__(self):
        return f"<Habit {self.text[:20]}... ({self.id})>"

    @hybrid_property
    def current_streak(self) -> int:
        return self._current_streak

    @current_streak.setter
    def current_streak(self, value):
        if self.best_streak is None:
            self.best_streak = 0
        if int(value) > self.best_streak:
            self.best_streak = value
        self._current_streak = value

    @current_streak.expression
    def current_streak(cls):
        return cls._current_streak

    @hybrid_property
    def progress(self):
        """
        Динамическое свойство progress, получаемое из таблицы HabitProgress.
        Возвращает список кортежей (date, completed).
        """
        if self.interval == HabitPeriod.DAILY:
            date_filter = datetime.now().date() - timedelta(weeks=4) # прогресс за последние 30 дней
        elif self.interval == HabitPeriod.WEEKLY:
            date_filter = datetime.now().date() - timedelta(weeks=24)  # прогресс за последние 180 дней
        else:
            date_filter = datetime.now().date() - timedelta(weeks=48)  # прогресс за последние 360 дней
        # потом можно настроить для custom_interval тоже

        return [(record.record_date, record.completed) for record in self.progress_records if record.record_date >= date_filter]


class HabitProgress(BaseModel):
    __tablename__ = "habit_progress"

    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    record_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)

    # Отношения
    habit = relationship("Habit", back_populates="progress_records")

    # Ограничения
    __table_args__ = (
        UniqueConstraint('habit_id', 'record_date', name='uq_habit_date'),
    )

    def __repr__(self):
        return f"<HabitProgress habit={self.habit_id} date={self.record_date}>"
