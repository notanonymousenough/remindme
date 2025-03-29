from uuid import UUID

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class ReminderSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID напоминания")
    user_id: UUID = Field(None, description="ID пользователя, создавшего напоминание")
    text: str = Field(..., description="Текст напоминания")
    time: datetime = Field(..., description="Время напоминания")
    tags: Optional[List[str]] = Field(None, description="Список тегов")
    status: Optional[str] = Field(None, description="Статус напоминания")
    removed: Optional[bool] = Field(None, description="Признак удаления напоминания")
    created_at: Optional[datetime] = Field(datetime.now(), description="Время создания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")
    completed_at: Optional[datetime] = Field(None, description="Время выполнения")
    notification_sent: Optional[bool] = Field(None, description="Признак отправки уведомления")

    class Config:
        from_attributes = True


class ReminderSchemaToEdit(BaseModel):
    id: UUID = Field(..., description="reminder ID")
    text: str = Field(None, description="Новый текст напоминания")
    time: datetime = Field(None, description="Новое время напоминания")
    tags: Optional[List[str]] = Field(None, description="Список тегов")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")


class ReminderSchemaToEditTime(BaseModel):
    id: UUID = Field(..., description="reminder ID")
    time: datetime = Field(..., description="Новое время напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")


class ReminderSchemaToComplete(BaseModel):
    id: UUID = Field(..., description="reminder ID")
    time: datetime = Field(..., description="Новое время напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")


class ReminderMarkAsCompleteSchema(BaseModel):
    id: UUID = Field(..., description="reminder ID")
    status: Optional[str] = Field(None, description="Статус напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")
    completed_at: Optional[datetime] = Field(datetime.now(), description="Время выполнения")


class ReminderToDeleteSchema:
    id: UUID = Field(..., description="reminder ID to delete")