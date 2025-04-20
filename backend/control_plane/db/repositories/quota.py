from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models import Quota, QuotaUsage
from backend.control_plane.db.models.quota import ResourceType
from backend.control_plane.db.repositories.base import BaseRepository
from backend.control_plane.db.repositories.role import UserRoleRepository


class ResourceTypeRepository(BaseRepository[ResourceType]):
    def __init__(self):
        super().__init__(ResourceType)

    async def get_resource_type_by_name(self, session: AsyncSession, name: str) -> ResourceType:
        """Получение квоты для определенного ресурса"""
        stmt = select(self.model).where(
            and_(
                ResourceType.name == name
            )
        )
        result = await session.execute(stmt)
        return result.scalars().one_or_none()


class QuotaRepository(BaseRepository[Quota]):
    def __init__(self):
        super().__init__(Quota)

    async def get_limit_for_resource(self, session: AsyncSession, role_id: UUID, resource_type_id: UUID) -> int:
        """Получение квоты для определенного ресурса"""
        stmt = select(self.model).where(
            and_(
                Quota.role_id == role_id,
                Quota.resource_type_id == resource_type_id
            )
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

    async def update_resource_usage(self, user_id: UUID, resource_type: str, increment_value: float = 1):
        await self.create(user_id, resource_type=resource_type, date=func.current_date(), usage_value=increment_value)

    async def check_resource_limit(self, user_id: UUID, resource_type_name: str, increment_value: float = 1) -> bool:
        """Проверка, не превышен ли лимит ресурса"""
        async with await get_async_session() as session:
            role_id = await self.user_role_repo.get_user_active_role(session, user_id)
            resource_type = await self.resource_type_repo.get_resource_type_by_name(session, resource_type_name)
            limit = await self.quota_repo.get_limit_for_resource(session, role_id, resource_type.id)

            if limit == -1:
                return True

            # Проверка различных типов лимитов
            if resource_type.endswith('_daily'):
                current_usage = await self.get_user_daily_usage(session, user_id, resource_type.id)
                return (current_usage + increment_value) <= limit
            elif resource_type.endswith('_monthly'):
                current_usage = await self.get_user_monthly_usage(session, user_id, resource_type.id)
                return (current_usage + increment_value) <= limit
            else:
                current_usage = await self.get_user_resource_usage(session, user_id, resource_type.id)
                return (current_usage + increment_value) <= limit

    async def get_user_daily_usage(self, session: AsyncSession, user_id: UUID, resource_type_id: UUID) -> float:
        """Get user's daily usage for a specific resource type"""
        stmt = select(func.coalesce(func.sum(QuotaUsage.usage_value), 0)).where(
            and_(
                QuotaUsage.user_id == user_id,
                QuotaUsage.resource_type == resource_type_id,
                QuotaUsage.date == func.current_date()
            )
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())

    async def get_user_monthly_usage(self, session: AsyncSession, user_id: UUID, resource_type_id: UUID) -> float:
        """Get user's monthly usage for a specific resource type"""
        stmt = select(func.coalesce(func.sum(QuotaUsage.usage_value), 0)).where(
            and_(
                QuotaUsage.user_id == user_id,
                QuotaUsage.resource_type == resource_type_id,
                func.extract('year', QuotaUsage.date) == func.extract('year', func.current_date()),
                func.extract('month', QuotaUsage.date) == func.extract('month', func.current_date())
            )
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())

    async def get_user_resource_usage(self, session: AsyncSession, user_id: UUID, resource_type_id: UUID) -> float:
        """Get user's total usage for a specific resource type (without time constraints)"""
        stmt = select(func.coalesce(func.sum(QuotaUsage.usage_value), 0)).where(
            and_(
                QuotaUsage.user_id == user_id,
                QuotaUsage.resource_type == resource_type_id
            )
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())
