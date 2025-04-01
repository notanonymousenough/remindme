import hmac
from http.client import HTTPException
from typing import Annotated

from fastapi.params import Depends
import jwt

from backend.control_plane.config import get_settings
from backend.control_plane.schemas.user import UserSchema, UserTelegramDataSchema
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


def generate_hash(data):
    sorted_params = sorted(f"{x}={y}" for x, y in data.items())
    data_check_bytes = "\n".join(sorted_params).encode()
    computed_hash = hmac.new(settings.bot_token_hash_bytes, data_check_bytes, "sha256")
    return computed_hash.hexdigest()


def has_correct_hash(request: UserTelegramDataSchema) -> bool:
    data = request.model_dump()
    expected_hash = data.pop("hash")
    computed_hash = generate_hash(data)
    return hmac.compare_digest(computed_hash, expected_hash)
