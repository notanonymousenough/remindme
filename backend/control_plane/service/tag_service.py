from typing import Sequence, Any, Union
from uuid import UUID

from backend.control_plane.db.repositories.tag import TagRepository
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema


class TagService:
    def __init__(self):
        self.repo = TagRepository()

    async def get_tag(self, tag_id: UUID) -> TagSchema:
        response = await self.repo.get_by_model_id(model_id=tag_id)
        return TagSchema.model_validate(response)

    async def get_tags_by_user_id(self, user_id: UUID) -> Sequence[TagSchema]:
        response = await self.repo.get_models(user_id=user_id)
        return [TagSchema.model_validate(tag) for tag in response]

    async def update_tag(self, tag_id: UUID, request: TagRequestSchema) -> bool:
        response = await self.repo.update_model(model_id=tag_id, **request.model_dump())
        tag_schema = TagSchema.model_validate(response)
        if tag_schema:
            return True
        return False

    async def add_tag(self, user_id: UUID, tag: TagRequestSchema) -> TagSchema:
        tag_model = tag.model_dump(exclude_none=True, exclude_unset=True)
        response = await self.repo.create(user_id=user_id, **tag_model)
        return TagSchema.model_validate(response)

    async def delete_tag(self, user_id: UUID, tag_id: UUID) -> bool:
        return await self.repo.delete_model(user_id=user_id, model_id=tag_id)

    async def add_tags_to_reminder(self, tags: Sequence[UUID], reminder_id: UUID) -> bool:
        return await self.repo.add_tags_to_reminder(tags, reminder_id)

    async def delete_tag_from_reminder(self, tag_id: UUID, reminder_id: UUID):
        return await self.repo.delete_tag_from_reminder(tag_id=tag_id, reminder_id=reminder_id)

    async def get_links_tags_id_from_reminder_id(self, reminder_id: UUID) -> Sequence[UUID]:
        return await self.repo.get_links_tags_id_from_reminder_id(reminder_id=reminder_id)

    async def get_links_reminders_id_from_tag_id(self, tag_id: UUID) -> Sequence[UUID]:
        return await self.repo.get_links_reminders_id_from_tag_id(tag_id=tag_id)

    async def get_tags_info_from_reminder_id(self, reminder_id: UUID) -> Union[Sequence[TagSchema], None]:
        tags_id = await self.get_links_tags_id_from_reminder_id(reminder_id=reminder_id)
        tags = [await self.repo.get_by_model_id(model_id=tag_id) for tag_id in tags_id]

        if tags:
            return [TagSchema.model_validate(tag) for tag in tags]
        return None


_tag_service = TagService()


def get_tag_service():
    return _tag_service
