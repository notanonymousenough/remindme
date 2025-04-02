from fastapi import APIRouter

tag_router = APIRouter(
    prefix="/tag",
    tags=["Tag"]
)

