from typing import Sequence
from uuid import UUID

from sqlalchemy import insert, delete, and_
from sqlalchemy.future import select

from .base import BaseRepository
from ..engine import get_async_session
from ..models import reminder_tags
from ..models.tag import Tag


class TagRepository(BaseRepository[Tag]):
    def __init__(self):
        super().__init__(Tag)

    async def add_tag_to_reminder(self, tag_id: UUID, reminder_id: UUID) -> bool:  # in reminder_tags table
        async with get_async_session() as session:
            stmt = insert(reminder_tags).values(
                tag_id=tag_id,
                reminder_id=reminder_id
            )
            try:
                await session.execute(stmt)
                await session.commit()
                return True
            except Exception as e:
                print(f"Error adding tag to reminder: {e}")
                await session.rollback()
                return False

    async def add_tags_to_reminder(self, tag_ids: Sequence[UUID], reminder_id: UUID, session=None):
        # TODO: add decorator for session provider or some better solution
        if not session:
            async with await get_async_session() as session:
                return await self.__add_tags_to_reminder(tag_ids, reminder_id, session)
        else:
            return await self.__add_tags_to_reminder(tag_ids, reminder_id, session)

    async def __add_tags_to_reminder(self, tag_ids: Sequence[UUID], reminder_id: UUID, session):
        for tag_id in tag_ids:
            stmt = insert(reminder_tags).values(
                tag_id=tag_id,
                reminder_id=reminder_id
            )
            try:
                await session.execute(stmt)
            except Exception as e:
                print(f"Error adding tag to reminder: {e}")
                await session.rollback()
                return False
        await session.commit()
        return True

    async def delete_tag_from_reminder(self, tag_id: UUID, reminder_id: UUID) -> bool:
        async with get_async_session() as session:
            stmt = delete(reminder_tags).where(
                and_(
                    getattr(reminder_tags, "reminder_id") == reminder_id,
                    getattr(reminder_tags, "tag_id") == tag_id,
                )
            )
            try:
                await session.execute(stmt)
                await session.commit()
                return True
            except Exception as e:
                print(f"Error deleting tag from reminder: {e}")
                await session.rollback()
                return False

    async def get_links_tags_id_from_reminder_id(self, reminder_id: UUID) -> Sequence[UUID]:
        async with get_async_session() as session:
            stmt = select(reminder_tags.c.tag_id).where(
                and_(
                    reminder_tags.c.reminder_id == reminder_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_links_reminders_id_from_tag_id(self, tag_id: UUID) -> Sequence[UUID]:
        async with get_async_session() as session:
            stmt = select(reminder_tags.c.reminder_id).where(
                and_(
                    reminder_tags.c.tag_id == tag_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()


_tag_repo = TagRepository()


def get_tag_repo():
    return _tag_repo
