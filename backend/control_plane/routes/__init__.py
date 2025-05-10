from backend.control_plane.routes.achievement import achievement_router
from backend.control_plane.routes.auth import auth_router
from backend.control_plane.routes.habit import habit_router
from backend.control_plane.routes.reminder import reminder_router
from backend.control_plane.routes.removed import removed_router
from backend.control_plane.routes.tag import tag_router
from backend.control_plane.routes.user import user_router

list_of_routes = [
    auth_router,
    reminder_router,
    user_router,
    tag_router,
    habit_router,
    removed_router,
    achievement_router
]


__all__ = [
    "list_of_routes",
]
