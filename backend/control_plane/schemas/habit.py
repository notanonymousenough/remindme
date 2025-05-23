from datetime import datetime, date
from typing import Optional, Sequence, List
from uuid import UUID

from pydantic import Field, BaseModel

from backend.control_plane.db.models import HabitInterval


class HabitSchemaResponse(BaseModel):
    id: UUID = Field(...)
    user_id: UUID = Field(..., description="ID пользователя")
    text: str = Field(..., description="Текст привычки")

    interval: HabitInterval = Field(..., description="Периодичность привычки")
    custom_interval: Optional[str] = Field(None, description="Пользовательский период (для period=custom)")

    progress: Optional[List] = Field(..., description="Прогресс выполнения array")  # из habit_progress

    current_streak: int = Field(..., description="Текущая серия")
    best_streak: int = Field(..., description="Лучшая серия")  # сам высчитывается в модели sqlalchemy

    start_date: date = Field(..., description="Дата начала")  # когда начинает действовать, дефолт datetime.now()
    end_date: Optional[date] = Field(None, description="Дата окончания")  # когда привычка неактивна становится
    removed: bool = Field(..., description="Признак удаления")

    created_at: Optional[datetime] = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(..., description="Время последнего обновления")

    class Config:
        from_attributes = True
