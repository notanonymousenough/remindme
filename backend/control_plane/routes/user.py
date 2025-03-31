from typing import Annotated, Optional, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.dependencies.models import SecurityRequirement
from fastapi.params import Cookie
from starlette import status
from starlette.requests import Request

from jose import JWTError, jwt
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
        # _: Request,
        # user_service: Annotated[UserService, Depends(get_user_service)],
        token: str = Depends(get_settings().OAUTH2_SCHEME),
        # user: UserSchema = Depends(get_authorized_user)
):
    print(token)
    user_id = get_user_id_from_access_token(token)
    return await user_service.get_user(user_id=user_id)
