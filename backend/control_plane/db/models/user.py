from sqlalchemy import Column, String, Date, Integer, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel, SexType


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    sex = Column(Enum(SexType))
    first_name = Column(String(255))
    last_name = Column(String(255))
    birth_date = Column(Date)
    telegram_id = Column(String(255), unique=True)
    calendar_integration_key = Column(String(255))
    timezone = Column(String(100), default="UTC")
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_active = Column(DateTime(timezone=True), server_default=func.now())

    # Определение отношений с другими моделями
    #tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    #reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    #habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    #achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    #neuro_images = relationship("NeuroImage", back_populates="user")
    # statistics = relationship("UserStatistics", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.id})>"
