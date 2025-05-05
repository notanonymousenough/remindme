from .habit_state_actions.new_habit import new_habit_router
from .habits import habits_router
from .reminder_state_actions.edit_reminder import edit_reminder_router
from .reminder_state_actions.new_reminder import new_reminder_router
from .reminders import reminders_router
from .start import start_router
from .tag_state_actions.edit_tag import edit_tag_router
from .tag_state_actions.new_tag import new_tag_router
from .tags import tags_router

list_of_routers = [
    reminders_router,
    start_router,
    habits_router,
    tags_router,
    new_habit_router,
    edit_tag_router,
    new_tag_router,
    edit_reminder_router,
    new_reminder_router
 ]

__all__ = [
    "reminders_router",
    "start_router",
    "habits_router",
    list_of_routers
]