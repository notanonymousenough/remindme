from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# user achievement
class AchievementSchema(BaseModel):
    id: UUID = Field(..., description='ID')
    user_id: Optional[UUID] = Field(...,)
    template_id: Optional[UUID] = Field(..., )
    unlocked: Optional[bool] = Field(...,)
    unlocked_at: Optional[datetime] = Field(...,)
    progress: Optional[int] = Field(...,)
    updated_at: datetime = Field(...)
    created_at: datetime = Field(...)

    class Config:
        from_attributes = True
