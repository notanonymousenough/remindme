from typing import Optional
from uuid import UUID

from pydantic import Field, BaseModel


class TagSchema(BaseModel):
    id: UUID
    user_id: Optional[UUID] = Field(...)
    name: str = Field(...)
    color: Optional[str] = Field(None, description="#FFFFFF")
    emoji: str = Field(..., description="Emoji")

    class Config:
        from_attributes = True
