from typing import Optional

import emoji
from pydantic import Field, BaseModel, field_validator


class TagRequestSchema(BaseModel):
    name: str = Field(...)
    color: Optional[str] = Field(None, description="#FFFFFF")
    emoji: str = Field(..., description="Emoji")

    @field_validator("emoji")
    def validate_emoji_string(cls, value):
        if not emoji.is_emoji(value):
            raise ValueError("Значение должно быть emoji")
        return value

    class Config:
        from_attributes = True
