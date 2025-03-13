"""
Основной файл запуска data-plane
"""
import asyncio
import logging
import sys
from temporalio.client import Client
from temporalio.worker import Worker
from .config import settings
from .workflows import (
    reminder_workflows,
    habit_workflows,
    maintenance_workflows,
    statistic_workflows,
    integration_workflows
)
from .activities import (
    reminder_activities,
    habit_activities,
    neuro_activities,
    calendar_activities,
    achievement_activities
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("data_plane")


async def main():
    """Основная функция запуска worker'а Temporal"""
    logger.info(f"Запуск {settings.APP_NAME} v{settings.APP_VERSION}")

    # Подключение к Temporal
    client = await Client.connect(settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE)
    logger.info(f"Подключено к Temporal: {settings.TEMPORAL_HOST}")

    # Регистрация воркеров
    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[
            reminder_workflows.CheckRemindersWorkflow,
            reminder_workflows.SendReminderNotificationWorkflow,
            habit_workflows.ProcessHabitsWorkflow,
            habit_workflows.GenerateHabitImageWorkflow,
            maintenance_workflows.CleanupRemovedItemsWorkflow,
            statistic_workflows.UpdateUserStatisticsWorkflow,
            integration_workflows.SyncCalendarWorkflow
        ],
        activities=[
            reminder_activities.check_active_reminders,
            reminder_activities.mark_reminder_as_forgotten,
            reminder_activities.send_telegram_notification,
            habit_activities.update_habit_streaks,
            habit_activities.process_habit_progress,
            neuro_activities.generate_habit_image,
            calendar_activities.sync_calendar_events,
            achievement_activities.process_user_achievements
        ],
    )

    # Запуск воркеров
    logger.info(f"Запуск worker'а на очереди {settings.TEMPORAL_TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
