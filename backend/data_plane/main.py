import asyncio
import logging
import sys
from temporalio.client import Client
from temporalio.worker import Worker

from backend.data_plane.utils.schedulers import ensure_workflows_running
from config import settings
from backend.data_plane import activities
from backend.data_plane import workflows

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("data_plane")


async def main():
    logger.info(f"Запуск {settings.APP_NAME} v{settings.APP_VERSION}")

    # Подключение к Temporal
    client = await Client.connect(settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE)
    logger.info(f"Подключено к Temporal: {settings.TEMPORAL_HOST}")

    # Убедиться, что воркфлоу запущены
    await ensure_workflows_running(client)

    # Регистрация воркеров
    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[
            workflows.reminders.CheckRemindersWorkflow,
            workflows.reminders.SendReminderNotificationWorkflow,
        ],
        activities=[
            activities.reminders.check_active_reminders,
            activities.reminders.send_telegram_notification,
            activities.reminders.abort_sent
        ],
    )

    # Запуск воркеров
    logger.info(f"Запуск worker'а на очереди {settings.TEMPORAL_TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
