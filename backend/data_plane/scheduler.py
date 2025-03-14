"""
Планировщик задач для data-plane
Запускает периодические workflow через Temporal
"""
import asyncio
import logging
import sys
from datetime import timedelta
from temporalio.client import Client
from config import settings
from workflows.reminders import CheckRemindersWorkflow

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("scheduler")


async def schedule_check_reminders(client):
    """Запуск периодической проверки напоминаний (каждые 5 минут)"""
    try:
        workflow_id = "check_reminders_cron"

        # Проверяем существует ли уже такой workflow
        try:
            handle = client.get_workflow_handle(workflow_id)
            describe = await handle.describe()

            if describe.status.name in ("COMPLETED", "FAILED", "TERMINATED", "TIMED_OUT"):
                logger.info(f"Найден завершенный workflow {workflow_id}. Запускаем заново.")
            else:
                logger.info(f"Workflow {workflow_id} уже выполняется. Пропускаем.")
                return

        except Exception as e:
            # Если workflow не существует - создаем новый
            logger.info(f"Создание нового workflow {workflow_id}")

        # Запускаем workflow с cron-расписанием
        await client.start_workflow(
            CheckRemindersWorkflow.run,
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )
        logger.info(f"Workflow {workflow_id} успешно запланирован")

    except Exception as e:
        logger.error(f"Ошибка при запуске workflow проверки напоминаний: {str(e)}")


async def main():
    """Основная функция запуска всех периодических задач"""
    logger.info(f"Запуск планировщика задач v{settings.APP_VERSION}")

    # Подключение к Temporal
    client = await Client.connect(settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE)
    logger.info(f"Подключено к Temporal: {settings.TEMPORAL_HOST}")

    # Запуск всех периодических задач
    await schedule_check_reminders(client)

    # TODO: добавить задачу которая будет помечать старые невыполненные и неперенесенные напоминалки в forgotten?

    logger.info("Все задачи успешно запланированы")


if __name__ == "__main__":
    asyncio.run(main())
