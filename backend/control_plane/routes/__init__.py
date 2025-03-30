from backend.control_plane.routes.auth import auth_router
from backend.control_plane.routes.reminder import reminder_router


list_of_routes = [
    auth_router,
    reminder_router,
]


__all__ = [
    "list_of_routes",
]
