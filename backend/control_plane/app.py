import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.control_plane.routes import reminder_router, auth_router
from backend.control_plane.routes.user import user_router
from backend.control_plane.utils.openapi_schema import custom_openapi

app = FastAPI()

app.include_router(reminder_router)
app.include_router(auth_router)
app.include_router(user_router)


app.openapi_schema = custom_openapi(app)

uvicorn.run(app=app)
