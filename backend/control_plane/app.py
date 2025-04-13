import uvicorn
from fastapi import FastAPI, Request

from backend.control_plane.config import get_settings
from backend.control_plane.middlewares.log_request import start_logging
from backend.control_plane.routes import reminder_router, auth_router
from backend.control_plane.routes.habit import habit_router
from backend.control_plane.routes.tag import tag_router
from backend.control_plane.routes.user import user_router
from backend.control_plane.utils.openapi_schema import custom_openapi

app = FastAPI()

app.include_router(reminder_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(tag_router)
app.include_router(habit_router)

app.openapi_schema = custom_openapi(app)

if get_settings().DEBUG:
    start_logging(app)

uvicorn.run(app=app)
