from fastapi import FastAPI
from uvicorn import run

from backend.control_plane.config import DefaultSettings, get_settings
from backend.control_plane.routes import list_of_routes
from backend.control_plane.utils.openapi_schema import custom_openapi


def bind_routes(application: FastAPI, setting: DefaultSettings) -> None:
    """
    Bind all routes to application.
    """
    for route in list_of_routes:
        application.include_router(route, prefix=setting.PATH_PREFIX)


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

@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    settings_for_application = get_settings()
    run(
        "backend.control_plane.__main__:app",
        host=settings_for_application.APP_ADDRESS,
        port=settings_for_application.APP_PORT,
        reload=True,
        reload_dirs=["backend/control_plane", "tests"],
        log_level="debug",
    )
