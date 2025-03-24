import uvicorn
from fastapi import FastAPI

from backend.control_plane.routes import reminder_router, auth_router
from backend.control_plane.routes.user import user_router

app = FastAPI()
app.include_router(reminder_router)
app.include_router(auth_router)
app.include_router(user_router)


uvicorn.run(app=app)
