from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from ..models.tag import Tag
from .base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Tag)

    async def get_by_user(self, user_id: UUID) -> List[Tag]:
        """Получение всех тегов пользователя"""
        stmt = select(Tag).where(Tag.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_name(self, user_id: UUID, name: str) -> Optional[Tag]:
        """Получение тега пользователя по имени"""
        stmt = select(Tag).where(
            and_(
                Tag.user_id == user_id,
                Tag.name == name
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def replace_tag(self, old_tag_id: UUID, new_tag_id: UUID) -> bool:
        """
        Замена тега во всех напоминаниях
        Используется при удалении тега с указанием замены
        """
        # Здесь выполняем SQL-запрос для замены тега в таблице reminder_tags
        stmt = """
        UPDATE reminder_tags
        SET tag_id = :new_tag_id
        WHERE tag_id = :old_tag_id
        """
        await self.session.execute(stmt, {"old_tag_id": old_tag_id, "new_tag_id": new_tag_id})
        await self.session.flush()
        return True
