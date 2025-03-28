from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.remindme_api.db import get_session


api_router = APIRouter(
    prefix="/auth",
    tags=["User"],
)


@api_router.post(
    "/telegram",
    status_code=status.HTTP_200_OK)
async def telegram():
    pass
