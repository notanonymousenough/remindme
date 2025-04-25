import enum
import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


# Определение перечислений для типов данных
class SexType(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class ReminderStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FORGOTTEN = "FORGOTTEN"


class HabitInterval(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class AchievementCategory(str, enum.Enum):
    REMINDER = "REMINDER"
    HABIT = "HABIT"
    SYSTEM = "SYSTEM"


class ImageRate(str, enum.Enum):
    GOOD = "GOOD"
    NEUTRAL = "NEUTRAL"
    BAD = "BAD"


class ImageStatus(str, enum.Enum):
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"


# Базовая модель с общими полями
class BaseModel(DeclarativeBase):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
