import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HabitProgressPydantic(BaseModel):
    habit_id: UUID = Field(..., description="ID привычки")
    date: datetime.date = Field(..., description="Дата выполнения")
    completed: bool = Field(default=False, description="Признак выполнения")

    class Config:
        orm_mode = True