from datetime import datetime, timedelta
from typing import Annotated

import jwt

from fastapi import APIRouter, HTTPException, Depends, Body

from backend.config import get_settings
from backend.control_plane.schemas.user import UserTelegramDataSchema
from backend.control_plane.service.user_service import get_user_service, UserService
from backend.control_plane.utils.auth import has_correct_hash

auth_router = APIRouter(
    prefix="/v1/auth",
    tags=["Auth"],
)

settings = get_settings()


@auth_router.post("/telegram")
async def auth_telegram(
        user_service: Annotated[UserService, Depends(get_user_service)],
        request: UserTelegramDataSchema = Body(...)
):
    if not get_settings().DEBUG and not has_correct_hash(request):
        raise HTTPException(401, detail="Invalid Telegram hash")

    request = UserTelegramDataSchema.model_validate(request)
    user = await user_service.create_or_update_user_from_telegram_data(request)

    jwt_token = jwt.encode(
        {
            "exp": datetime.now() + timedelta(hours=3),
            "user_id": str(user.id)
        },
        get_settings().SECRET_KEY,
        algorithm="HS256"
    )

    return {"access_token": jwt_token, "token_type": "bearer"}
