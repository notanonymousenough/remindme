from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from sqlalchemy import Column, Text, Date, Boolean, ForeignKey, Enum, Integer, UniqueConstraint, DateTime
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
    progress_records = relationship("HabitProgress", back_populates="habit",
                                    cascade="all, delete-orphan")  # lazy='...'?
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
    def progress(self) -> List[dict]:
        """
        Динамическое свойство progress, получаемое из таблицы HabitProgress
        """

        # потом можно настроить для custom_interval тоже
        dates = self.generate_date_sequence()
        dates_dict = [
            {
                "date": date,
                "completed": False
            } for date in dates
        ]
        records_dict = [
            {
                "date": record.record_date,
                "completed": record.completed
            }
            for record in self.progress_records if record.record_date >= dates[0]
        ]

        def merge(main: List[dict], second: List[dict]) -> List[dict]:
            """
            Args:
                main: dates that created with api
                second: all dates (depends on HabitPeriod and function generate_date_sequence())
            Returns:
                list with second dates, but with replace with main list
            """
            main_sequence = [item["date"] for item in main]
            merged = []
            for item in main:
                merged.append(item)
            for item in second:
                if item["date"] in main_sequence:
                    continue
                merged.append(item)
            return merged

        return sorted(merge(records_dict, dates_dict), key=lambda x: x["date"])

    def generate_date_sequence(self) -> List[datetime.date]:
        """
        Генерирует список дат от date_filter до сегодняшней даты,
        с шагом, зависящим от HabitPeriod (daily, weekly, monthly).

        Returns:
            list[datetime.date]: Список дат.
        """

        today = datetime.now().date()
        dates = []

        if self.interval == HabitPeriod.DAILY:
            date_filter = datetime.now().date() - timedelta(days=30)  # прогресс за последние 30 дней
            dates = [date_filter + timedelta(days=i) for i in range((today - date_filter).days + 1)]
        elif self.interval == HabitPeriod.WEEKLY:
            date_filter = datetime.now().date() - timedelta(days=180)  # прогресс за последние 180 дней, раз в неделю
            dates = [date_filter + timedelta(weeks=i) for i in range(
                ((today - date_filter).days // 7) + 2)]  # +2 для запаса, чтобы точно захватить последнюю неделю
        elif self.interval == HabitPeriod.MONTHLY:
            date_filter = datetime.now().date() - timedelta(weeks=52)  # прогресс за последний год, раз в месяц
            dates = [date_filter + relativedelta(months=i) for i in range(
                ((today.year - date_filter.year) * 12 + (today.month - date_filter.month)) + 2)]  # +2
        else:
            raise ValueError("HabitPeriod должен быть 'daily', 'weekly' или 'monthly'")

        return dates

    @progress.expression
    def progress(cls):
        return None


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
