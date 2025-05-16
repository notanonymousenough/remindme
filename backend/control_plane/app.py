import logging

import uvicorn
from fastapi import FastAPI

from backend.config import get_settings, DefaultSettings
from backend.control_plane.middlewares.log_request import start_debug_logging
from backend.control_plane.routes import list_of_routes
from backend.control_plane.utils.openapi_schema import custom_openapi


def bind_routes(application: FastAPI, setting: DefaultSettings) -> None:
    """
    Bind all routes to application.
    """
    for route in list_of_routes:
        application.include_router(route, prefix=setting.PATH_PREFIX)  # in fut. we can set prefix individual for route


def get_app() -> FastAPI:
    """
    Creates application and all dependable objects.
    """

    application = FastAPI(
        title="Remind Me control-plane",
    )
    settings = get_settings()
    bind_routes(application, settings)
    application.openapi_schema = custom_openapi(application)
    return application


app = get_app()

if __name__ == "__main__":
    settings = get_settings()

    logging.basicConfig(level=getattr(logging, get_settings().LOG_LEVEL))

    if settings.DEBUG:
        start_debug_logging(app)

    uvicorn.run(
        app=app,
        host=settings.APP_ADDRESS,
        port=settings.APP_PORT,
    )
