from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, join
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from ..models.achievement import AchievementTemplate, UserAchievement, AchievementCategory
from .base import BaseRepository


class AchievementTemplateRepository(BaseRepository[AchievementTemplate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AchievementTemplate)

    async def get_by_category(self, category: AchievementCategory) -> List[AchievementTemplate]:
        """Получение шаблонов достижений по категории"""
        stmt = select(AchievementTemplate).where(AchievementTemplate.category == category)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class UserAchievementRepository(BaseRepository[UserAchievement]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserAchievement)

    async def get_by_user(self, user_id: UUID) -> List[UserAchievement]:
        """Получение всех достижений пользователя"""
        stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user_with_templates(self, user_id: UUID) -> List[dict]:
        """Получение всех достижений пользователя с данными шаблонов"""
        stmt = select(
            UserAchievement, AchievementTemplate
        ).join(
            AchievementTemplate,
            UserAchievement.template_id == AchievementTemplate.id
        ).where(
            UserAchievement.user_id == user_id
        )

        result = await self.session.execute(stmt)
        achievements = []

        for user_achievement, template in result:
            achievement_data = {
                "id": user_achievement.id,
                "user_id": user_achievement.user_id,
                "template_id": user_achievement.template_id,
                "unlocked": user_achievement.unlocked,
                "unlocked_at": user_achievement.unlocked_at,
                "progress": user_achievement.progress,
                "name": template.name,
                "description": template.description,
                "icon_url": template.icon_url,
                "condition": template.condition,
                "category": template.category.value
            }
            achievements.append(achievement_data)

        return achievements

    async def get_unlocked_by_user(self, user_id: UUID) -> List[UserAchievement]:
        """Получение разблокированных достижений пользователя"""
        stmt = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.unlocked == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_template(self, user_id: UUID, template_id: UUID) -> Optional[UserAchievement]:
        """Получение достижения пользователя по шаблону"""
        stmt = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.template_id == template_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def unlock(self, user_achievement_id: UUID, unlocked_at: Optional[datetime] = None) -> Optional[
        UserAchievement]:
        """Разблокировка достижения"""
        if not unlocked_at:
            unlocked_at = datetime.now()
        return await self.update(
            user_achievement_id,
            unlocked=True,
            unlocked_at=unlocked_at,
            progress=100
        )

    async def update_progress(self, user_achievement_id: UUID, progress: int) -> Optional[UserAchievement]:
        """Обновление прогресса достижения"""
        # Проверяем, что прогресс не превышает 100%
        progress = min(100, max(0, progress))

        achievement = await self.get(user_achievement_id)
        if not achievement:
            return None

        # Если прогресс достиг 100%, автоматически разблокируем достижение
        if progress == 100 and not achievement.unlocked:
            return await self.unlock(user_achievement_id)

        return await self.update(
            user_achievement_id,
            progress=progress
        )

    async def ensure_user_achievements(self, user_id: UUID) -> List[UserAchievement]:
        """
        Убеждаемся, что у пользователя созданы записи для всех доступных шаблонов достижений
        """
        # Получаем все существующие шаблоны
        template_stmt = select(AchievementTemplate)
        template_result = await self.session.execute(template_stmt)
        templates = template_result.scalars().all()

        # Получаем существующие достижения пользователя
        user_achievement_stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)
        user_achievement_result = await self.session.execute(user_achievement_stmt)
        existing_achievements = user_achievement_result.scalars().all()

        # Находим шаблоны, для которых у пользователя нет достижений
        existing_template_ids = {achievement.template_id for achievement in existing_achievements}
        missing_templates = [template for template in templates if template.id not in existing_template_ids]

        # Создаем недостающие достижения
        created_achievements = []
        for template in missing_templates:
            achievement = await self.create(
                user_id=user_id,
                template_id=template.id,
                unlocked=False,
                progress=0
            )
            created_achievements.append(achievement)

        # Возвращаем все достижения пользователя
        return existing_achievements + created_achievements
