from typing import Annotated

from fastapi import APIRouter, Depends

from backend.control_plane.config import get_settings
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.user_service import UserService, get_user_service
from backend.control_plane.utils.auth import get_user_id_from_access_token

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.post("/")
async def add_user(
        request: UserSchema,
        user_service: Annotated[UserService, Depends(get_user_service)],
        token: str = Depends(get_settings().OAUTH2_SCHEME)
):
    user_id = request.id
    return await user_service.repo.create(user_id=user_id, **vars(request))


@user_router.get("/")
async def get_user(
        user_service: Annotated[UserService, Depends(get_user_service)],
        token: str = Depends(get_settings().OAUTH2_SCHEME)
):
    user_id = get_user_id_from_access_token(token)
    return await user_service.get_user(user_id=user_id)
