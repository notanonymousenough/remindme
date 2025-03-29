from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi.params import Path
from pydantic import BaseModel, Field

from backend.control_plane.db.models import ReminderStatus


class ReminderToEditRequestSchema(BaseModel):
    id: UUID = Path(..., description="reminder ID")
    text: str = Field(None, description="Новый текст напоминания")
    time: datetime = Field(None, description="Новое время напоминания")
    tags: Optional[List[str]] = Field(None, description="Список тегов")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")


class ReminderToEditTimeRequestSchema(BaseModel):
    id: UUID = Path(..., description="reminder ID")
    time: datetime = Field(..., description="Новое время напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")


class ReminderMarkAsCompleteRequestSchema(BaseModel):
    id: UUID = Path(..., description="reminder ID")
    status: Optional[str] = Field(ReminderStatus.COMPLETED, description="Статус напоминания")
    updated_at: Optional[datetime] = Field(datetime.now(), description="Время последнего обновления")
    completed_at: Optional[datetime] = Field(datetime.now(), description="Время выполнения")


class ReminderToDeleteRequestSchema:
    id: UUID = Path(..., description="reminder ID to delete")
