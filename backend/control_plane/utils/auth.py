from http.client import HTTPException
from typing import Annotated

from fastapi.requests import Request

from fastapi.params import Depends
import jwt

from backend.control_plane.config import get_settings
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.user_service import get_user_service, UserService

settings = get_settings()


async def get_current_user(
        request: Request,
        user_service: Annotated[UserService, Depends(get_user_service())]
) -> UserSchema:
    auth_exception = HTTPException(401, "Authentication is required")
    if not (token := request.cookies.get(settings.AUTH_COOKIE_NAME)):
        raise auth_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise auth_exception
    if not (user_id := payload.get_by_model_id("user_id")):
        raise auth_exception
    if not (user := await user_service.get_user_by_user_id(user_id)):
        raise auth_exception
    return user


async def generate_hash(user_):
    pass