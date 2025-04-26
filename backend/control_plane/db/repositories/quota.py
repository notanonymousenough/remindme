import logging
from datetime import date
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models import Quota, QuotaUsage, Role, User
from backend.control_plane.db.models.quota import ResourceType
from backend.control_plane.db.repositories.base import BaseRepository
from backend.control_plane.db.repositories.role import UserRoleRepository

logger = logging.getLogger("quota_repository")


class ResourceTypeRepository(BaseRepository[ResourceType]):
    def __init__(self):
        super().__init__(ResourceType)

    async def get_resource_type_by_name(self, session: AsyncSession, name: str) -> ResourceType:
        stmt = select(self.model).where(ResourceType.name == name)
        result = await session.execute(stmt)
        return result.scalars().one_or_none()


class QuotaRepository(BaseRepository[Quota]):
    def __init__(self):
        super().__init__(Quota)

    async def get_limit_for_resource(self, session: AsyncSession, role_id: UUID, resource_type_id: UUID) -> int:
        stmt = select(self.model).where(
            Quota.role_id == role_id,
            Quota.resource_type_id == resource_type_id
        )
        result = await session.execute(stmt)
        quota = result.scalars().one_or_none()

        if not quota:
            # Безлимит, если квота не определена
            return -1

        return quota.max_value


class QuotaUsageRepository(BaseRepository[QuotaUsage]):
    def __init__(self):
        super().__init__(QuotaUsage)
        self.quota_repo = QuotaRepository()
        self.user_role_repo = UserRoleRepository()
        self.resource_type_repo = ResourceTypeRepository()

    async def update_resource_usage(self, user_id: UUID, resource_type_name: str, increment_value: float = 1):
        today = date.today()
        async with await get_async_session() as session:
            async with session.begin():
                resource_type_obj = await self.resource_type_repo.get_resource_type_by_name(session, resource_type_name)
                if not resource_type_obj:
                    logger.error(f"Resource type {resource_type_name} not found")
                    return False

                existing = await session.execute(
                    select(QuotaUsage).where(
                        QuotaUsage.user_id == user_id,
                        QuotaUsage.resource_type_id == resource_type_obj.id,
                        QuotaUsage.date == today
                    )
                )

                existing = existing.scalar_one_or_none()

                if existing:
                    existing.usage_value += increment_value
                else:
                    new_usage = QuotaUsage(
                        user_id=user_id,
                        resource_type_id=resource_type_obj.id,
                        date=today,
                        usage_value=increment_value
                    )
                    session.add(new_usage)

                return True

    async def check_resource_limit(self, user_id: UUID, resource_type_name: str, increment_value: float = 1) -> bool:
        """Проверка, не превышен ли лимит ресурса"""
        async with await get_async_session() as session:
            role_id = await self.user_role_repo.get_user_active_role(session, user_id)
            resource_type = await self.resource_type_repo.get_resource_type_by_name(session, resource_type_name)

            if not resource_type:
                logger.error(f"Resource type {resource_type_name} not found")
                return False

            limit = await self.quota_repo.get_limit_for_resource(session, role_id, resource_type.id)

            if limit == -1:
                return True

            # Проверка различных типов лимитов
            if resource_type_name.endswith('_daily'):
                current_usage = await self.get_user_daily_usage(session, user_id, resource_type.id)
                return (current_usage + increment_value) <= limit
            elif resource_type_name.endswith('_monthly'):
                current_usage = await self.get_user_monthly_usage(session, user_id, resource_type.id)
                return (current_usage + increment_value) <= limit
            else:
                current_usage = await self.get_user_resource_usage(session, user_id, resource_type.id)
                return (current_usage + increment_value) <= limit

    async def get_user_daily_usage(self, session: AsyncSession, user_id: UUID, resource_type_id: UUID) -> float:
        """Get user's daily usage for a specific resource type"""
        stmt = select(func.coalesce(func.sum(QuotaUsage.usage_value), 0)).where(
            QuotaUsage.user_id == user_id,
            QuotaUsage.resource_type_id == resource_type_id,
            QuotaUsage.date == func.current_date()
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())

    async def get_user_monthly_usage(self, session: AsyncSession, user_id: UUID, resource_type_id: UUID) -> float:
        """Get user's monthly usage for a specific resource type"""
        stmt = select(func.coalesce(func.sum(QuotaUsage.usage_value), 0)).where(
            QuotaUsage.user_id == user_id,
            QuotaUsage.resource_type_id == resource_type_id,
            func.extract('year', QuotaUsage.date) == func.extract('year', func.current_date()),
            func.extract('month', QuotaUsage.date) == func.extract('month', func.current_date())
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())

    async def get_user_resource_usage(self, session: AsyncSession, user_id: UUID, resource_type_id: UUID) -> float:
        """Get user's total usage for a specific resource type (without time constraints)"""
        stmt = select(func.coalesce(func.sum(QuotaUsage.usage_value), 0)).where(
            QuotaUsage.user_id == user_id,
            QuotaUsage.resource_type_id == resource_type_id
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())

    async def check_and_increment_resource_count(self, user_id: UUID, resource_type_name: str, increment: int = 1) -> bool:
        async with await get_async_session() as session:
            try:
                # Начинаем транзакцию
                async with session.begin():
                    # Сначала получаем resource_type_id
                    resource_type_id = await self.resource_type_repo.get_resource_type_by_name(session, resource_type_name)

                    if resource_type_id is None:
                        logger.warning(f"Resource type {resource_type_name} not found")
                        return False

                    # Получаем роль пользователя
                    role_id = await self.user_role_repo.get_user_active_role(session, user_id)

                    # Получаем максимальное значение квоты для данного типа ресурса
                    max_value = await self.quota_repo.get_limit_for_resource(session, role_id, resource_type_id)

                    if max_value is None:
                        logger.warning(f"No quota defined for user {user_id} and resource {resource_type_name}")
                        return False

                    # Если лимит -1, то он не ограничен
                    if max_value == -1:
                        return True

                    # Получаем текущее использование
                    today = date.today()
                    usage_query = select(QuotaUsage.usage_value).where(
                        QuotaUsage.user_id == user_id,
                        QuotaUsage.resource_type_id == resource_type_id,
                        QuotaUsage.date == today
                    )
                    usage_result = await session.execute(usage_query)
                    current_usage = usage_result.scalar_one_or_none() or 0

                    # Проверяем, не будет ли превышен лимит
                    if current_usage + increment > max_value:
                        return False

                    # Обновляем использование атомарно
                    existing_usage = await session.execute(
                        select(QuotaUsage).where(
                            QuotaUsage.user_id == user_id,
                            QuotaUsage.resource_type_id == resource_type_id,
                            QuotaUsage.date == today
                        )
                    )
                    existing_usage = existing_usage.scalar_one_or_none()

                    if existing_usage:
                        existing_usage.usage_value += increment
                    else:
                        # Создаем новую запись
                        new_usage = QuotaUsage(
                            user_id=user_id,
                            resource_type_id=resource_type_id,
                            date=today,
                            usage_value=increment
                        )
                        session.add(new_usage)

                    return True

            except SQLAlchemyError as e:
                logger.error(f"Error in check_and_increment_resource_count: {e}")
                return False

    async def check_and_decrement_resource_count(self, user_id: UUID, resource_type: str, decrement: int = 1) -> bool:
        """
        Атомарно уменьшает счетчик использования ресурса.
        Полезно при удалении ресурсов (напоминаний, привычек).

        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса
            decrement: Количество удаляемых ресурсов

        Returns:
            bool: True, если операция выполнена успешно
        """
        async with await get_async_session() as session:
            try:
                async with session.begin():
                    today = date.today()
                    resource_type_id = await session.execute(
                        select(ResourceType.id).where(ResourceType.name == resource_type)
                    )
                    resource_type_id = resource_type_id.scalar_one()

                    existing_usage = await session.execute(
                        select(QuotaUsage).where(
                            QuotaUsage.user_id == user_id,
                            QuotaUsage.resource_type_id == resource_type_id,
                            QuotaUsage.date == today
                        )
                    )
                    existing_usage = existing_usage.scalar_one_or_none()

                    if existing_usage:
                        # Уменьшаем значение, но не ниже 0
                        existing_usage.usage_value = max(0, existing_usage.usage_value - decrement)

                    return True

            except SQLAlchemyError as e:
                logger.error(f"Error in check_and_decrement_resource_count: {e}")
                return False

    async def get_current_resource_count(self, user_id: UUID, resource_type: str) -> int:
        """
        Получает текущее количество использованных ресурсов.

        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса

        Returns:
            int: Текущее количество использованных ресурсов
        """
        async with await get_async_session() as session:
            try:
                today = date.today()
                query = select(QuotaUsage.usage_value).where(
                    QuotaUsage.user_id == user_id,
                    QuotaUsage.resource_type_id == select(ResourceType.id).where(
                        ResourceType.name == resource_type
                    ).scalar_subquery(),
                    QuotaUsage.date == today
                )
                result = await session.execute(query)
                return result.scalar_one_or_none() or 0
            except SQLAlchemyError as e:
                logger.error(f"Error in get_current_resource_count: {e}")
                return 0
