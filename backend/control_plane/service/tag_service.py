from typing import Sequence
from uuid import UUID

from backend.control_plane.db.repositories.tag import TagRepository
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema


class TagService:
    def __init__(self):
        self.repo = TagRepository()

    async def get_tags(self, user_id: UUID) -> Sequence[TagSchema]:
        return await self.repo.get_tags(user_id=user_id)

    async def add_tag(self, user_id: UUID, tag: TagRequestSchema) -> TagSchema:
        return await self.repo.add_tag(user_id=user_id, tag=tag)

    async def delete_tag(self, user_id: UUID, tag_id: UUID) -> bool:
        return await self.repo.delete_tag(user_id=user_id, tag_id=tag_id)

    async def add_tags_to_reminder(self, tags: Sequence[UUID], reminder_id: UUID) -> bool:
        for tag_id in tags:
            try:
                await self.repo.add_tag_to_reminder(tag_id=tag_id, reminder_id=reminder_id)
                print(f"Тэг {tag_id} добавлен в reminder {reminder_id}.")
            except Exception as ex:
                print(f"Тэг {tag_id} не добавлен: {ex}")
        return True

    async def delete_tag_from_reminder(self, tag_id: UUID, reminder_id: UUID):
        return await self.repo.delete_tag_from_reminder(tag_id=tag_id, reminder_id=reminder_id)


_tag_service = TagService()


def get_tag_service():
    return _tag_service
