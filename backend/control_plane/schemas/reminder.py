import uuid
from uuid import UUID

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Sequence

from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.schemas.tag import TagSchema


class ReminderSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID напоминания")  # назначается в db/models/base
    user_id: Optional[UUID] = Field(None, description="ID пользователя, создавшего напоминание")
    text: str = Field(..., description="Текст напоминания")
    time: datetime = Field(..., description="Время напоминания")
    tags: Optional[List[TagSchema]] = Field(..., description="Список тегов")
    status: Optional[str] = Field(ReminderStatus.ACTIVE, description="Статус напоминания")
    removed: Optional[bool] = Field(None, description="Признак удаления напоминания")
    created_at: Optional[datetime] = Field(datetime.now(), description="Время создания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")
    completed_at: Optional[datetime] = Field(None, description="Время выполнения")
    notification_sent: Optional[bool] = Field(None, description="Признак отправки уведомления")

    class Config:
        from_attributes = True
