import enum
import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from ..engine import Base


# Определение перечислений для типов данных
class SexType(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class ReminderStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FORGOTTEN = "forgotten"


class HabitPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class AchievementCategory(str, enum.Enum):
    REMINDER = "reminder"
    HABIT = "habit"
    SYSTEM = "system"


class ImageStatus(str, enum.Enum):
    GOOD = "good"
    NEUTRAL = "neutral"
    BAD = "bad"


# Базовая модель с общими полями
class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
