from typing import Annotated, Sequence, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Body, HTTPException

from backend.config import get_settings
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.tag_service import TagService, get_tag_service
from backend.control_plane.utils.auth import get_authorized_user

tag_router = APIRouter(
    prefix="/tag",
    tags=["Tag"]
)


@tag_router.post(
    path="/",

)
async def tag_add(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    request: TagRequestSchema = Body(...),
    user: UserSchema = Depends(get_authorized_user)
) -> Union[TagSchema, bool]:
    if len(await tag_service.get_tags_by_user_id(user.id)) > get_settings().TAGS_MAX_LENGTH:
        raise HTTPException(
            422,
            "Reached max length of tags!"
        )
    return await tag_service.add_tag(user_id=user.id, tag=request)


@tag_router.get(
    path="/",

)
async def get_tags(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    user: UserSchema = Depends(get_authorized_user)
) -> Sequence[TagSchema]:
    return await tag_service.get_tags_by_user_id(user_id=user.id)


@tag_router.delete(
    path="/{tag_id}",
)
async def delete_tag(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    tag_id: UUID,
    user: UserSchema = Depends(get_authorized_user)
):
    return await tag_service.delete_tag(user_id=user.id, tag_id=tag_id)

