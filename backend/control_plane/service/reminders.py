from backend.control_plane.db.schemas import Reminder


class RemindersService(AbstractService):
    def __init__(self, context):
        context = ...

    def get_reminders(self, user_id) -> List[Reminder]:
        reminder_models = context.get_remoinders_repository().get_active_by_user(user_id)

        result = []
        for reminder_model in reminder_models:
            result.append(Reminder.model_validate(reminder_model))

        return result
