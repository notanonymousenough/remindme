from sqlalchemy import insert, delete, and_
from sqlalchemy.future import select
from typing import List, Sequence
from uuid import UUID

from ..engine import get_async_session
from ..models import reminder_tags
from ..models.tag import Tag
from .base import BaseRepository
from ...schemas.requests.tag import TagRequestSchema
from ...schemas.tag import TagSchema


class TagRepository(BaseRepository[Tag]):
    def __init__(self):
        super().__init__(Tag)

    async def get_tags(self, user_id: UUID) -> Sequence[TagSchema]:
        response = await self.get_models(user_id=user_id)
        return [TagSchema.model_validate(tag) for tag in response]

    async def add_tag(self, user_id: UUID, tag: TagRequestSchema) -> TagSchema:
        tag_model = tag.model_dump(exclude_none=True, exclude_unset=True)
        response = await self.create(user_id=user_id, **tag_model)
        return TagSchema.model_validate(response)

    async def delete_tag(self, user_id: UUID, tag_id: UUID) -> bool:
        return await self.delete_model(user_id=user_id, model_id=tag_id)

    async def add_tag_to_reminder(self, tag_id: UUID, reminder_id: UUID) -> bool:  # in reminder_tags table
        async with await get_async_session() as session:
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

    async def delete_tag_from_reminder(self, tag_id: UUID, reminder_id: UUID) -> bool:
        async with await get_async_session() as session:
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
