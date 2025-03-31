import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.control_plane.routes import reminder_router, auth_router
from backend.control_plane.routes.user import user_router

app = FastAPI()

app.include_router(reminder_router)
app.include_router(auth_router)
app.include_router(user_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My Telegram Auth API",
        version="1.0.0",
        description="This API uses Telegram Access Tokens for authentication. Authenticate via Telegram Login to get an access token.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "TelegramAccessToken": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",  # или другой формат
            "description": "Telegram Access Token authentication. Obtain a token via Telegram Login and use it in the 'Authorization' header as 'Bearer <token>'.",
        }
    }
    return openapi_schema


app.openapi_schema = custom_openapi()

uvicorn.run(app=app)
