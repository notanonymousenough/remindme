from typing import Annotated

from falcon import HTTP_404
from fastapi import APIRouter, Depends, Body
from starlette.status import HTTP_200_OK

from backend.control_plane.schemas.requests.user import UserUpdateRequest
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.user_service import UserService, get_user_service
from backend.control_plane.utils.auth import get_authorized_user

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.put("/")
async def update_user(
        user_service: Annotated[UserService, Depends(get_user_service)],
        request: UserUpdateRequest = Body(...)
) -> UserSchema:
    return await user_service.update_user(request=request)


@user_router.get("/")
async def get_user(
        user: UserSchema = Depends(get_authorized_user)
) -> UserSchema:
    return user


@user_router.delete("/")
async def delete_me(
        user_service: Annotated[UserService, Depends(get_user_service)],
        user: UserSchema = Depends(get_authorized_user)
):
    response = await user_service.delete_user(user.id)
    if response:
        return HTTP_200_OK
    return HTTP_404
