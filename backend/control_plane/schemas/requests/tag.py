from typing import Optional
from uuid import UUID

from pydantic import Field, BaseModel


class TagRequestSchema(BaseModel):
    name: str = Field(...)
    color: Optional[str] = Field(None, description="#FFFFFF")
    emoji: str = Field(..., description="Emoji")

    class Config:
        from_attributes = True
