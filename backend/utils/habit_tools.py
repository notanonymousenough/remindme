from backend.control_plane.db.models import HabitInterval
from backend.control_plane.schemas.habit import HabitSchemaResponse

HABIT_PERIOD_NAMES = {
    HabitInterval.DAILY: "месяц",
    HabitInterval.WEEKLY: "полгода",
    HabitInterval.MONTHLY: "год"
}

HABIT_PERIOD_NAMES_INTERVAL = {
    HabitInterval.DAILY: "сегодня",
    HabitInterval.WEEKLY: "на этой неделе",
    HabitInterval.MONTHLY: "в этом месяце"
}

STATUS_EMOJI = {
    False: "❌",
    True: "✅"
}

STATUS_WORD = {
    False: "не выполняли",
    True: "выполняли"
}


def get_last_record_status(habit: HabitSchemaResponse, emoji_flag=False) -> str:
    status = habit.progress[-1]["completed"]
    return STATUS_WORD[status] if not emoji_flag else STATUS_EMOJI[status]


def get_last_record_status_bool(habit: HabitSchemaResponse) -> bool:
    return habit.progress[-1]["completed"]


def get_completed_record_sum(habit: HabitSchemaResponse) -> int:
    return sum(record["completed"] for record in habit.progress)
