from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status


auth_router = APIRouter(
    prefix="/auth",
    tags=["User"],
)


@auth_router.post(
    "/telegram",
    status_code=status.HTTP_200_OK)
async def telegram():
    pass
