"""
Репозиторий для работы с достижениями
"""
from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.future import select

from ..engine import get_async_session
from ..models.achievement import AchievementTemplate, UserAchievement
from .base import BaseRepository


class AchievementTemplateRepository(BaseRepository[AchievementTemplate]):
    def __init__(self):
        super().__init__(AchievementTemplate)


class UserAchievementRepository(BaseRepository[UserAchievement]):
    def __init__(self):
        super().__init__(UserAchievement)

    async def get_unlocked_achievements(self, user_id: UUID) -> Sequence[UserAchievement]:
        """
        Получает разблокированные достижения пользователя
        """
        async with get_async_session() as session:
            stmt = select(UserAchievement).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.unlocked == True
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_achievement_by_template(self, user_id: UUID, template_id: UUID) -> Optional[UserAchievement]:
        """
        Получает достижение пользователя по ID шаблона
        """
        async with get_async_session() as session:
            stmt = select(UserAchievement).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.template_id == template_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().one_or_none()
