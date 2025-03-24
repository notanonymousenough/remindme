from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Path

from backend.control_plane.schemas.reminder import ReminderSchema
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.reminder_service import get_reminder_service, RemindersService
from backend.control_plane.service.user_service import UserService, get_user_service

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.post("/")
async def add_user(
        request: UserSchema,
        user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.repo.create(**vars(request))


@user_router.get("/")
async def get_user(
        user_service: Annotated[UserService, Depends(get_user_service)]
):
    pass  # Arsen: need to learn about authentication
