from datetime import date, datetime
from uuid import UUID

from fastapi.params import Path
from pydantic import Field, BaseModel


class HabitProgressRequest(BaseModel):
    habit_id: UUID = Path(...)

    record_date: date = Field(datetime.now().date(), description="Дата отметки")
    completed: bool = Field(True, description="Выполнена или нет")

    class Config:
        from_attributes = True
