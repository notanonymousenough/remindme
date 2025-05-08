from datetime import datetime, date
from typing import Optional
from uuid import UUID

from fastapi.params import Path
from pydantic import Field, BaseModel

from backend.control_plane.db.models import HabitInterval


class HabitSchemaPostRequest(BaseModel):
    text: str = Field(..., description="Текст привычки")

    # привычку можно выполнить раз в *interval*
    interval: HabitInterval = Field(HabitInterval.DAILY, description="Периодичность привычки")
    custom_interval: Optional[str] = Field(None, description="Пользовательский период (для period=custom)")

    current_streak: int = Field(0, description="Текущая серия")

    start_date: date = Field(datetime.now().date(), description="Дата начала")
    end_date: Optional[date] = Field(default=None, description="Когда привычка станет неактивной")

    class Config:
        from_attributes = True


class HabitSchemaPutRequest(BaseModel):  # EDIT Schema
    habit_id: UUID = Path(...)
    text: Optional[str] = Field(..., description="Текст привычки")

    interval: Optional[HabitInterval] = Field(..., description="Периодичность привычки")
    custom_interval: Optional[str] = Field(..., description="Пользовательский период (для period=custom)")

    end_date: Optional[date] = Field(..., description="Когда привычка станет неактивной")
    removed: Optional[bool] = Field(..., description="Признак удаления")

    class Config:
        from_attributes = True


# Habit Progress
class HabitProgressSchemaPostRequest(BaseModel):
    habit_id: UUID = Path(...)

    record_date: date = Field(datetime.now().date(), description="Дата отметки")
    completed: bool = Field(True, description="Выполнена или нет")

    class Config:
        from_attributes = True
