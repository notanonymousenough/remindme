from http.client import HTTPResponse

from fastapi import APIRouter


from fastapi import APIRouter, Body, Depends, HTTPException, Request

from backend.bot.routers.reminders import return_to_menu
from backend.control_plane.schemas.reminders import RemindersGetRequest

api_router = APIRouter(
    prefix="/reminder",
    tags=["Reminder"],
)


@api_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationSuccess,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad parameters for registration",
        },
    },
)
async def registration(
    request: RemindersGetRequest,
    context: Depends(get_app_context)
    session: Depends(get_session)
):
    result = context.get_reminders_service().get_reminders(session.user_id)
    if result is not None and len(result) > 0:
        return result
    return HTTPResponse("not found")