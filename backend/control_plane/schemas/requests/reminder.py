from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi.params import Path
from pydantic import BaseModel, Field

from backend.control_plane.db.models import ReminderStatus


class ReminderToEditRequestSchema(BaseModel):
    id: UUID = Path(..., description="reminder ID")
    text: str = Field(None, description="Новый текст напоминания")
    time: Optional[datetime] = Field(None, description="Новое время напоминания")
    tags: Optional[List[UUID]] = Field(None, description="Список тегов")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")

    class Config:
        from_attributes = True


class ReminderToEditTimeRequestSchema(BaseModel):
    id: UUID = Path(..., description="reminder ID")
    time: datetime = Field(..., description="Новое время напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")

    class Config:
        from_attributes = True


class ReminderMarkAsCompleteRequestSchema(BaseModel):
    id: UUID = Path(..., description="reminder ID")
    status: Optional[str] = Field(ReminderStatus.COMPLETED, description="Статус напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")
    completed_at: Optional[datetime] = Field(datetime.now(), description="Время выполнения")

    class Config:
        from_attributes = True


class ReminderAddSchemaRequest(BaseModel):
    text: str = Field(..., description="Текст напоминания")
    time: datetime = Field(..., description="Время напоминания")
    tags: Optional[List[str]] = Field(..., description="Список тегов")
    status: Optional[str] = Field(ReminderStatus.ACTIVE, description="Статус напоминания")
    created_at: Optional[datetime] = Field(datetime.now(), description="Время создания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")

    class Config:
        from_attributes = True


class ReminderChangeTagsRequest(BaseModel):
    id: UUID = Field(..., description="reminder ID")
    tags: Optional[List[str]] = Field(..., description="Список тегов")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")

    class Config:
        from_attributes = True
