from backend.control_plane.routes.auth import api_router as auth_router
from backend.control_plane.routes.reminder import api_router as reminder_router


list_of_routes = [
    auth_router,
    reminder_router,
]


__all__ = [
    "list_of_routes",
]
