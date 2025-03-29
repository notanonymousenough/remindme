from typing import Annotated

from fastapi import APIRouter, Body
from fastapi.params import Depends

from backend.control_plane.schemas.image_response import ImageSchema
from backend.control_plane.schemas.requests.neuroimage import NeuroImageRequest
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.image_service import ImageService, get_image_service
from backend.control_plane.utils.auth import get_authorized_user

images_router = APIRouter(
    prefix="/image",
    tags=["Image"]
)


@images_router.get(
    path="/",
    responses={
        200: {
            "description": "Список нейроизображений"
        }
    },
    response_model=ImageSchema
)
async def neuroimage_get(
        image_service: Annotated[ImageService, Depends(get_image_service)],
        user: Annotated[UserSchema, Depends(get_authorized_user)],
        request: NeuroImageRequest = Body(...)
) -> ImageSchema:
    return image_service.neuroimages_by_entity_ids(
        user_id=user.id,
        reminder_id=request.reminder_id,
        habit_id=request.habit_id,
        limit=request.limit,
        offset=request.offset)
