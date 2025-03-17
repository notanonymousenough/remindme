from fastapi import APIRouter

api_router = APIRouter(
    prefix="/reminder",
    tags=["Reminder"],
)
