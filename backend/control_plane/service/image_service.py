from uuid import UUID

from backend.control_plane.db.repositories.neuro_image import NeuroImageRepository
from backend.control_plane.schemas.image_response import ImageSchema


class ImageService:
    def __init__(self):
        self.repo = NeuroImageRepository()

    def neuroimages_by_entity_ids(self,
                                  user_id: UUID,
                                  reminder_id: UUID,
                                  habit_id: UUID,
                                  limit: int,
                                  offset: int):
        response = self.repo.get_models(user_id=user_id, **{"reminder_id": reminder_id, "habit_id": habit_id})
        return ImageSchema.model_validate(response)


_image_service = ImageService()


def get_image_service():
    return _image_service
