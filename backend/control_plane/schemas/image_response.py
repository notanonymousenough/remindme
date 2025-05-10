from uuid import UUID

from pydantic import BaseModel, Field

from backend.control_plane.db.models import ImageStatus


class ImageSchema(BaseModel):
    id: UUID = Field(..., description="id")
    user_id: UUID = Field(..., description="ID пользователя")
    prompt: str = Field(..., description="Текст prompt")
    habit: UUID = Field(...,)
    reminder_id: UUID = Field(...)
    image_url: str = Field(...)
    thumbnail_url: str = Field(...)
    status: ImageStatus = Field(...)
