import asyncio
from datetime import timedelta

from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleCalendarSpec, ScheduleRange, \
    ScheduleAlreadyRunningError
from temporalio.common import RetryPolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from backend.config import get_settings
from backend.data_plane.workflows.achievements import CheckUserAchievementsWorkflow
from backend.data_plane.workflows.calendar import SyncCalendarsWorkflow
from backend.data_plane.workflows.habits import StartImagesGenerationWorkflow
from backend.data_plane.workflows.maintenance import CleanupRemovedItemsWorkflow
from backend.data_plane.workflows.morning import MorningMessageWorkflow
from backend.data_plane.workflows.reminders import CheckRemindersWorkflow


async def ensure_workflows_running(client):
    """Запускает воркфлоу, если они ещё не запущены."""
    async def start_if_not_exists(workflow_type, workflow_id):
        try:
            await client.start_workflow(
                workflow_type,
                id=workflow_id,
                task_queue=get_settings().TEMPORAL_TASK_QUEUE,
                execution_timeout=None,
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=0,  # Бесконечные ретраи
                ),
            )
            print(f"Workflow {workflow_id} запущен")
        except WorkflowAlreadyStartedError:
            print(f"Workflow {workflow_id} уже запущен")

    async def schedule_if_not_scheduled(workflow_type, workflow_id, schedule_calendar_spec):
        try:
            await client.create_schedule(
                f"{workflow_id}-schedule",
                Schedule(
                    action=ScheduleActionStartWorkflow(
                        workflow_type.run,
                        id=workflow_id,
                        task_queue=get_settings().TEMPORAL_TASK_QUEUE,
                    ),
                    spec=ScheduleSpec(
                        calendars=[schedule_calendar_spec]
                    ),
                ),
            )
            print(f"Workflow {workflow_id} запланирован")
        except ScheduleAlreadyRunningError:
            print(f"Workflow {workflow_id} уже запланирован")

    await asyncio.gather(
        start_if_not_exists(CheckRemindersWorkflow, "check-reminders"),
        start_if_not_exists(SyncCalendarsWorkflow, "sync-calendars"),
        schedule_if_not_scheduled(MorningMessageWorkflow, "morning-message", ScheduleCalendarSpec(hour=(ScheduleRange(6),))),
        schedule_if_not_scheduled(CheckUserAchievementsWorkflow, "check-achievements", ScheduleCalendarSpec(minute=(ScheduleRange(0),))),
        schedule_if_not_scheduled(StartImagesGenerationWorkflow, "start-images-generation", ScheduleCalendarSpec(day_of_month=(ScheduleRange(27),))),
        schedule_if_not_scheduled(CleanupRemovedItemsWorkflow, "cleanup-removed-items", ScheduleCalendarSpec(day_of_week=(ScheduleRange(6),))),
    )
