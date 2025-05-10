from datetime import datetime, date
from typing import Optional
from uuid import UUID

from fastapi.params import Path
from pydantic import Field, BaseModel

from backend.control_plane.db.models import HabitPeriod


class HabitPostRequest(BaseModel):
    text: str = Field(..., description="Текст привычки")

    # привычку можно выполнить раз в *interval*
    interval: HabitPeriod = Field(HabitPeriod.DAILY, description="Периодичность привычки")
    custom_interval: Optional[str] = Field(None, description="Пользовательский период (для period=custom)")

    current_streak: int = Field(0, description="Текущая серия")

    start_date: date = Field(datetime.now().date(), description="Дата начала")
    end_date: Optional[date] = Field(default=None, description="Когда привычка станет неактивной")

    class Config:
        from_attributes = True


class HabitPutRequest(BaseModel):
    habit_id: UUID = Path(...)
    text: Optional[str] = Field(None, description="Текст привычки")

    end_date: Optional[date] = Field(None, description="Когда привычка станет неактивной")
    removed: Optional[bool] = Field(None, description="Признак удаления")

    class Config:
        from_attributes = True


# Habit Progress
class HabitProgressRequest(BaseModel):
    habit_id: UUID = Path(...)

    record_date: date = Field(datetime.now().date(), description="Дата отметки")
    completed: bool = Field(True, description="Выполнена или нет")

    class Config:
        from_attributes = True
