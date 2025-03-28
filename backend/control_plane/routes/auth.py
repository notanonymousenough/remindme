from datetime import datetime
from typing import Annotated

import jwt
import hmac

from fastapi import APIRouter, HTTPException, Query
from fastapi.params import Depends
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

from backend.control_plane.config import get_settings
from backend.control_plane.db.engine import get_async_session
from backend.control_plane.schemas.user import UserTelegramDataSchema
from backend.control_plane.service.user_service import get_user_service, UserService

auth_router = APIRouter(
    prefix="/auth",
    tags=["User"],
)

settings = get_settings()


def has_correct_hash(request: Request) -> bool:
    """More on this here: https://core.telegram.org/widgets/login#checking-authorization"""
    params = request.query_params._dict
    expected_hash = params.pop("hash")
    sorted_params = sorted(f"{x}={y}" for x, y in params.items())
    data_check_bytes = "\n".join(sorted_params).encode()
    computed_hash = hmac.new(settings.bot_token_hash_bytes, data_check_bytes, "sha256")
    return hmac.compare_digest(computed_hash.hexdigest(), expected_hash)


@auth_router.get("/auth_telegram")
async def auth_telegram(
        request: Request,
        user_service: Annotated[UserService, Depends(get_user_service)],
        telegram_id: int = Query(alias="id"),
        first_name: str = Query(),
        username: str = Query(),
        photo_url: str = Query(),
        last_name: str = Query(),
        auth_date: datetime = Query(),
        hash: str = Query()
) -> RedirectResponse:
    async with await get_async_session() as session:
        if not has_correct_hash(request):
            raise HTTPException(401, detail="Authentication failed")

        await user_service.create_or_update_user(
            UserTelegramDataSchema(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                photo_url=photo_url,
                auth_date=auth_date,
                hash=hash
            ),
        )
        await session.commit()

        token = jwt.encode({"user_id": telegram_id}, get_settings().SECRET_KEY, algorithm="HS256")
        response = RedirectResponse("/")
        response.set_cookie(key=get_settings().AUTH_COOKIE_NAME, value=token)
        return response  # return {"access_token": "..."}
