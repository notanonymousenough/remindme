from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, join
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from ..models.achievement import AchievementTemplate, UserAchievement, AchievementCategory
from .base import BaseRepository


class AchievementTemplateRepository(BaseRepository[AchievementTemplate]):
    def __init__(self):
        super().__init__(AchievementTemplate)


class UserAchievementRepository(BaseRepository[UserAchievement]):
    def __init__(self):
        super().__init__(UserAchievement)
