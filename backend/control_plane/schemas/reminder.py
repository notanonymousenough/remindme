from uuid import UUID

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class ReminderSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID напоминания")
    user_id: UUID = Field(..., description="ID пользователя, создавшего напоминание")
    text: str = Field(..., description="Текст напоминания")
    time: datetime = Field(..., description="Время напоминания")
    #tags: Optional[List[str]] = Field(None, description="Список тегов")
    status: Optional[str] = Field(None, description="Статус напоминания")
    removed: Optional[bool] = Field(None, description="Признак удаления напоминания")
    created_at: Optional[datetime] = Field(datetime.now(), description="Время создания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")
    completed_at: Optional[datetime] = Field(None, description="Время выполнения")
    notification_sent: Optional[bool] = Field(None, description="Признак отправки уведомления")

    class Config:
        orm_mode = True


class ReminderSchemaToEdit(BaseModel):
    user_id: Optional[UUID] = Field(..., description="ID пользователя")
    text: str = Field(..., description="Новый текст напоминания")
    time: datetime = Field(..., description="Новое время напоминания")
    # tags: Optional[List[str]] = Field(None, description="Список тегов")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")


class ReminderSchemaTime(BaseModel):
    user_id: Optional[UUID] = Field(..., description="ID пользователя")
    time: datetime = Field(..., description="Новое время напоминания")
