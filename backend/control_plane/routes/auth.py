from datetime import datetime, timedelta
from typing import Annotated, Any, Coroutine

import jwt
import hmac

from fastapi import APIRouter, HTTPException, Query, Cookie
from fastapi.params import Depends
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from starlette.responses import RedirectResponse

from backend.control_plane.config import get_settings
from backend.control_plane.db.engine import get_async_session
from backend.control_plane.schemas.user import UserTelegramDataSchema
from backend.control_plane.service.user_service import get_user_service, UserService

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

settings = get_settings()


def has_correct_hash(request: UserTelegramDataSchema) -> bool:
    """More on this here: https://core.telegram.org/widgets/login#checking-authorization"""
    params = request.model_dump()
    expected_hash = params.pop("hash")

    sorted_params = sorted(f"{x}={y}" for x, y in params.items())
    data_check_bytes = "\n".join(sorted_params).encode()
    computed_hash = hmac.new(settings.bot_token_hash_bytes, data_check_bytes, "sha256")
    print(computed_hash.hexdigest())
    return hmac.compare_digest(computed_hash.hexdigest(), expected_hash)


@auth_router.post("/telegram")
async def auth_telegram(
        request: UserTelegramDataSchema,
        user_service: Annotated[UserService, Depends(get_user_service)]
):
    async with await get_async_session() as session:
        if get_settings().DEBUG or not has_correct_hash(request):
            raise HTTPException(401, detail="Invalid Telegram hash")

        await user_service.create_or_update_user(request)
        user = await user_service.get_user_by_telegram_id(telegram_id=request.telegram_id)  # get user from telegram_id

        jwt_token = jwt.encode(
            {
                "exp": datetime.now() + timedelta(hours=3),
                "user_id": str(user.id)
            },
            get_settings().SECRET_KEY,
            algorithm="HS256"
        )  # TODO(): вынести в отдельную функцюи в utils/auth

        return {"access_token": jwt_token, "token_type": "bearer"}
