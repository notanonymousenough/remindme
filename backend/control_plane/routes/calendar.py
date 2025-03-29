from fastapi import APIRouter

calendar_route = APIRouter(
    prefix="/calendar",
    tags=["Calendar"]
)
