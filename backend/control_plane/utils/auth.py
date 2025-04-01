from http.client import HTTPException
from typing import Annotated

from fastapi.params import Depends
import jwt

from backend.control_plane.config import get_settings
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.user_service import get_user_service, UserService

settings = get_settings()


async def get_authorized_user(
        user_service: Annotated[UserService, Depends(get_user_service)],
        token: str = Depends(get_settings().OAUTH2_SCHEME)
) -> UserSchema:
    try:
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid jwt token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(401, "Can't get user_id from payload")

    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(401, "user in None")

    return user


async def generate_hash(user_):
    pass
