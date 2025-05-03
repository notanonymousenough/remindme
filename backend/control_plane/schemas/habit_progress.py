from pydantic import BaseModel


class HabitProgressPydantic(BaseModel):
    habit_id: UUID = Field(..., description="ID привычки")
    date: date = Field(..., description="Дата выполнения")
    completed: bool = Field(default=False, description="Признак выполнения")

    class Config:
        orm_mode = True