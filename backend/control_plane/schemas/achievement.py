from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column

from backend.control_plane.db.models import AchievementCategory


class Achievement(BaseModel):
    id: UUID = Column(...)
    name: str = Column(..., nullable=False)
    description: str = Column(...)
    icon_url: str = Column(...)
    condition: str = Column(..., nullable=False)
    category: AchievementCategory = Column(..., nullable=False)


class UserAchivements(BaseModel):
    user_id: UUID = Column(...)
    template_id: UUID = Column(..., nullable=False)
    unlocked: bool = Column(..., default=False)
    unlocked_at: datetime = Column(...)
    progress: int = Column(..., default=0)
