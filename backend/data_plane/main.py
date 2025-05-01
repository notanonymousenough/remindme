import asyncio
import logging
import sys
from temporalio.client import Client
from temporalio.worker import Worker

from backend.data_plane.utils.schedulers import ensure_workflows_running
from backend.config import get_settings
from backend.data_plane import activities
from backend.data_plane import workflows

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, get_settings().LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("data_plane")


async def main():
    logger.info(f"Запуск remindme-data-plane")

    # Подключение к Temporal
    client = await Client.connect(get_settings().TEMPORAL_HOST, namespace=get_settings().TEMPORAL_NAMESPACE)
    logger.info(f"Подключено к Temporal: {get_settings().TEMPORAL_HOST}")

    # Убедиться, что воркфлоу запущены
    await ensure_workflows_running(client)

    # Регистрация воркеров
    worker = Worker(
        client,
        task_queue=get_settings().TEMPORAL_TASK_QUEUE,
        workflows=[
            workflows.reminders.CheckRemindersWorkflow,
            workflows.reminders.SendReminderNotificationWorkflow,
            workflows.morning.MorningMessageWorkflow,
            workflows.habits.StartImagesGenerationWorkflow,
            workflows.habits.GenerateHabitImageWorkflow,
            workflows.achievements.CheckUserAchievementsWorkflow,
            workflows.achievements.ProcessUserAchievementsWorkflow,
            workflows.calendar.SyncCalendarsWorkflow,
            workflows.calendar.UserCalendarSyncWorkflow,
        ],
        activities=[
            activities.reminders.check_active_reminders,
            activities.reminders.send_telegram_notification,
            activities.reminders.abort_sent,
            activities.morning.get_active_users,
            activities.morning.check_today_habits,
            activities.morning.check_today_reminders,
            activities.morning.send_telegram_message,
            activities.habits.check_active_habits,
            activities.habits.update_illustrate_habit_quota,
            activities.habits.get_habit_completion_rate,
            activities.habits.generate_image,
            activities.habits.update_describe_habit_text_quota,
            activities.habits.save_image_to_s3,
            activities.habits.save_image_to_db,
            activities.achievements.grant_achievement,
            activities.achievements.get_users_for_achievement_check,
            activities.achievements.check_user_achievements,
            activities.achievements.update_achievement_progress,
            activities.calendar.get_users_for_calendar_sync,
            activities.calendar.fetch_calendar_events,
            activities.calendar.sync_calendar_events,
            activities.calendar.handle_sync_errors,
        ],
    )

    # Запуск воркеров
    logger.info(f"Запуск worker'а на очереди {get_settings().TEMPORAL_TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
