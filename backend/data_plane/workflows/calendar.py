"""
Рабочие процессы для синхронизации с календарем
"""
import asyncio
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any

from temporalio.exceptions import ActivityError
from temporalio.workflow import ParentClosePolicy

with workflow.unsafe.imports_passed_through():
    from backend.data_plane.activities.calendar import (
        get_users_for_calendar_sync,
        fetch_calendar_events,
        sync_calendar_events,
        handle_sync_errors
    )
    import logging

logger = logging.getLogger("calendar_sync_workflows")


@workflow.defn
class SyncCalendarsWorkflow:
    """
    Рабочий процесс для периодической синхронизации календарей пользователей
    """

    @workflow.run
    async def run(self, iteration: int = 0):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        try:
            # Получаем список пользователей для синхронизации календаря
            users_for_sync = await workflow.execute_activity(
                get_users_for_calendar_sync,
                retry_policy=retry_policy,
                schedule_to_close_timeout=timedelta(minutes=5)
            )

            workflow.logger.info(f"Найдено {len(users_for_sync)} пользователей для синхронизации календаря")

            # Запускаем дочерние процессы для каждого пользователя
            for user_data in users_for_sync:
                await workflow.start_child_workflow(
                    UserCalendarSyncWorkflow.run,
                    user_data,
                    id=f"calendar_sync_{user_data['user_id']}_{iteration}",
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=10),
                        backoff_coefficient=2.0,
                        maximum_interval=timedelta(minutes=5),
                        maximum_attempts=2,
                    ),
                    parent_close_policy=ParentClosePolicy.ABANDON,
                )
        except Exception as e:
            workflow.logger.error(f"Ошибка в основном процессе синхронизации календаря: {e}")

        # Ждем перед следующей проверкой
        await asyncio.sleep(600)
        workflow.continue_as_new(iteration + 1)


@workflow.defn
class UserCalendarSyncWorkflow:
    """
    Рабочий процесс для синхронизации календаря конкретного пользователя
    """

    @workflow.run
    async def run(self, user_data: Dict[str, Any]):
        # Настраиваем политику повторных попыток
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        compensations = []  # Для компенсирующих операций в случае ошибки

        try:
            # Если события не смогут быть получены, добавляем компенсирующую операцию
            compensations.append(handle_sync_errors)

            # Получаем события из календаря
            events = await workflow.execute_activity(
                fetch_calendar_events,
                args=[user_data],
                retry_policy=retry_policy,
                schedule_to_close_timeout=timedelta(minutes=10)
            )

            # Если события получены, убираем компенсирующую операцию
            compensations = compensations[:-1]

            workflow.logger.info(f"Получено {len(events)} событий из календаря для пользователя {user_data['user_id']}")

            # Синхронизируем события с напоминаниями
            results = await workflow.execute_activity(
                sync_calendar_events,
                args=[user_data["user_id"], user_data["integration_id"], events],
                retry_policy=retry_policy,
                schedule_to_close_timeout=timedelta(minutes=15)
            )

            workflow.logger.info(
                f"Синхронизация календаря для {user_data['user_id']} завершена: "
                f"созданы {results['created']}, обновлены {results['updated']}, "
                f"удалены {results['deleted']}, без изменений {results['unchanged']}, "
                f"ошибки {results['errors']}"
            )

        except ActivityError as e:
            workflow.logger.error(f"Ошибка в активности синхронизации календаря: {e}")

            # Запускаем компенсирующие операции в обратном порядке
            for compensation_activity in reversed(compensations):
                try:
                    await workflow.execute_activity(
                        compensation_activity,
                        args=[user_data["user_id"], user_data["integration_id"], str(e)],
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=1),
                            maximum_attempts=2,
                        ),
                        schedule_to_close_timeout=timedelta(minutes=5)
                    )
                except Exception as comp_error:
                    workflow.logger.error(f"Ошибка в компенсирующей операции: {comp_error}")
