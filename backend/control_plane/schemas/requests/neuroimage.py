from uuid import UUID

from pydantic import BaseModel, Field


class NeuroImageRequest(BaseModel):
    reminder_id: UUID = Field(None, description="Reminder ID")
    habit_id: UUID = Field(None, description="Habit ID")
    limit: int = Field(10, description="Max count of images")
    offset: int = Field(0)
