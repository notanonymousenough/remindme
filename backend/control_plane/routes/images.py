from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends

from backend.control_plane.schemas.image_response import ImageSchema
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.image_service import ImageService
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
        removed_service: Annotated[ImageService, Depends()],
        user: Annotated[UserSchema, Depends(get_authorized_user)]
) -> ImageSchema:
    return
