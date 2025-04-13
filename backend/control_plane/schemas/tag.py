from datetime import datetime
from typing import Optional
from uuid import UUID

import emoji
from pydantic import Field, BaseModel, field_validator


class TagSchema(BaseModel):
    id: UUID
    user_id: Optional[UUID] = Field(...)
    name: str = Field(...)
    color: Optional[str] = Field(None, description="#FFFFFF")
    emoji: str = Field(..., description="Emoji")
    created_at: Optional[datetime] = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(..., description="Время последнего обновления")

    @field_validator("emoji")
    def validate_emoji_string(cls, value):
        if not emoji.is_emoji(value):
            raise ValueError("Значение должно быть emoji")
        return value

    class Config:
        from_attributes = True
