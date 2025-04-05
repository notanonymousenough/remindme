import asyncio
from datetime import timedelta

from temporalio.common import RetryPolicy
from temporalio.exceptions import WorkflowAlreadyStartedError
import temporalio

from backend.config import get_settings
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

    await asyncio.gather(
        start_if_not_exists(CheckRemindersWorkflow, "check-reminders"),
    )
