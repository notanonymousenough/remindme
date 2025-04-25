from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.models import Role, UserRole
from backend.control_plane.db.repositories.base import BaseRepository
from backend.control_plane.db.types.roles import DEFAULT_ROLE
from backend.control_plane.utils import timeutils


class RoleRepository(BaseRepository[Role]):
    def __init__(self):
        super().__init__(Role)


class UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self):
        super().__init__(UserRole)

    async def get_user_active_role(self, session: AsyncSession, user_id: UUID) -> UUID:
        """Получение активной роли пользователя"""
        now = timeutils.get_utc_now()
        stmt = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.valid_from <= now,
                (UserRole.valid_to.is_(None) | (UserRole.valid_to >= now))
            )
        ).order_by(UserRole.valid_from.desc())

        result = await session.execute(stmt)
        user_role = result.scalars().first()

        if not user_role:
            # Возвращаем базовую роль по умолчанию
            stmt = select(Role).where(
                and_(
                    Role.name == DEFAULT_ROLE
                )
            )
            result = await session.execute(stmt)
            basic_role = result.first()
            return basic_role.id

        return user_role.role_id
