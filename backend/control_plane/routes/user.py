from typing import Annotated

from fastapi import APIRouter, Depends

from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.user_service import UserService, get_user_service
from backend.control_plane.utils.auth import get_authorized_user

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.post("/")
async def update_user(
        user_service: Annotated[UserService, Depends(get_user_service)],
        user: UserSchema = Depends(get_authorized_user)
):
    return user_service.update_user(request=user)


@user_router.get("/")
async def get_user(
        user: UserSchema = Depends(get_authorized_user)
):
    return user
