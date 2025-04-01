import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.control_plane.routes import reminder_router, auth_router
from backend.control_plane.routes.user import user_router
from backend.control_plane.schemas.user import UserTelegramDataSchema


def custom_openapi(app):
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
            "bearerFormat": "JWT",
            "description": "Telegram Access Token authentication.\n\n"
                           "*To obtain an access token, use the `/auth/telegram` endpoint (POST request).*\n\n"
                           "Send the Telegram authentication data (as defined in `UserTelegramDataSchema`) in the request body to the `/auth/telegram` endpoint.\n\n"
                           "After successful authentication, the endpoint will return an `access_token`.\n\n"
                           "Use this `access_token` in the `Authorization` header for protected endpoints as `Bearer <access_token>`.\n\n"
                           "*Example Header:*\n\n"
                           "`Authorization: Bearer your_access_token_here`",
        }
    }

    if "/auth/telegram" in openapi_schema["paths"]:
        openapi_schema["paths"]["/auth/telegram"].update(
            {
                "post": {  # Теперь указываем "post" вместо "get", так как это POST запрос
                    "summary": "Obtain Telegram Access Token",
                    "description": "This endpoint is used to obtain a Telegram Access Token after successful Telegram Login.  \n\n"
                                   "*It's assumed you have already completed the Telegram Login process on the frontend.*\n\n"
                                   "Send the Telegram authentication data in the request body (as JSON) to this endpoint.  \n\n"
                                   "The data should conform to the `UserTelegramDataSchema` schema.",
                    "tags": ["Authentication"],
                    "requestBody": { # Описываем тело запроса
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserTelegramDataSchema" # Ссылка на схему UserTelegramDataSchema
                                }
                            }
                        },
                        "description": "Telegram authentication data received after successful Telegram Login.  \n\n"
                                       "*Schema:* `UserTelegramDataSchema`\n\n"
                                       "This data is usually provided by the Telegram Login Widget on the frontend and sent to this endpoint.",
                    },
                    "responses": {
                        "200": {
                            "description": "Successful authentication. Returns the access token.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "access_token": {
                                                "type": "string",
                                                "description": "The Telegram Access Token.",
                                            },
                                            "token_type": {
                                                "type": "string",
                                                "example": "bearer",
                                            },
                                        },
                                        "required": ["access_token"],
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": "Invalid Telegram authentication data.",
                            "content": {"application/json": {"example": {"detail": "Invalid Telegram auth data"}}},
                        },
                        "500": {"description": "Internal server error"},
                    },
                }
            }
        )
        # Добавляем схему UserTelegramDataSchema в components/schemas
        openapi_schema["components"]["schemas"]["UserTelegramDataSchema"] = UserTelegramDataSchema.schema()

    return openapi_schema
